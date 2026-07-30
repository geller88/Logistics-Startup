import json
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent
load_dotenv(base_dir / '.env')
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_REST_URL = f'{SUPABASE_URL}/rest/v1'

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError('Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your environment or .env file.')
if SUPABASE_SERVICE_ROLE_KEY.startswith('sb_publishable_'):
    raise RuntimeError('SUPABASE_SERVICE_ROLE_KEY must be the Supabase service role key, not a publishable anon key.')

SOURCES = [
    {'type': 'html', 'url': 'https://seedtable.com/best-logistics-startups'},
    {'type': 'html', 'url': 'https://www.crunchbase.com/hub/logistics-startups'},
    {'type': 'html', 'url': 'https://www.angel.co/companies?keywords=logistics'},
    {'type': 'html', 'url': 'https://www.producthunt.com/topics/logistics'},
    {'type': 'html', 'url': 'https://techcrunch.com/tag/logistics/'},
    {'type': 'html', 'url': 'https://www.eu-startups.com/tag/logistics/'},
    {'type': 'html', 'url': 'https://www.sifted.eu/tag/supply-chain/'},
    {'type': 'html', 'url': 'https://tech.eu/'},
    {'type': 'html', 'url': 'https://www.analyticsinsight.net/tag/logistics-startups/'},
    {'type': 'html', 'url': 'https://www.supplychaindive.com/tag/logistics/'},
    {'type': 'rss', 'url': 'https://www.freightwaves.com/feed/'},
    {'type': 'rss', 'url': 'https://www.supplychaindive.com/rss/all/'},
    {'type': 'rss', 'url': 'https://theloadstar.com/feed/'},
]

DIRECTORY_SOURCES = [
    {'type': 'html', 'url': 'https://seedtable.com/best-logistics-startups'},
    {'type': 'html', 'url': 'https://www.crunchbase.com/hub/logistics-startups'},
    {'type': 'html', 'url': 'https://www.angel.co/companies?keywords=logistics'},
    {'type': 'html', 'url': 'https://www.producthunt.com/topics/logistics'},
    {'type': 'html', 'url': 'https://techcrunch.com/tag/logistics/'},
]

HEADERS = {
    'User-Agent': 'logistics-startup-market-discoverer/1.0 (+https://example.com)',
}


def fetch_feed_items(feed_url, max_items=10):
    response = requests.get(feed_url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'xml')
    items = []

    for item in soup.find_all('item')[:max_items]:
        title = item.title.text.strip() if item.title else ''
        link = item.link.text.strip() if item.link else ''
        description = item.description.text.strip() if item.description else ''
        pub_date = item.pubDate.text.strip() if item.pubDate else ''
        items.append({
            'title': title,
            'link': link,
            'description': description,
            'published_at': pub_date,
        })

    return items


def should_keep_html_link(page_url, href, title):
    if not href or href.startswith('#') or href.startswith('mailto:') or href.startswith('javascript:'):
        return False
    title = title.strip()
    if len(title) < 4 or len(title) > 120:
        return False
    if re.search(r'\b(read more|click here|learn more|privacy policy|terms of use|contact us|cookies|login|subscribe|newsletter|signup|register|advertise|our team|about us|careers|jobs|events)\b', title, re.I):
        return False
    parsed = urlparse(href)
    if not parsed.scheme or not parsed.scheme.startswith('http'):
        return False
    blocked = [
        '/tag/', '/topic/', '/category/', '/author/', '/search/', '/newsletter/', '/privacy', '/terms',
        '/about', '/contact', '/cookies', '/login', '/signup', '/register', '/rss', '/feed', '/api',
        '/static', '/assets', '/events', '/press', '/subscribe', '/careers', '/jobs', '/sitemap', '/help',
    ]
    if any(seg in parsed.path.lower() for seg in blocked):
        return False
    if 'seedtable.com' in parsed.hostname and 'seedtable.com' not in page_url:
        return False
    if 'seedtable.com' in page_url and parsed.hostname and 'seedtable.com' in parsed.hostname:
        return False
    return True


def looks_like_company_name(title):
    title = title.strip()
    if not title or len(title) < 3 or len(title) > 80:
        return False
    if re.search(r'\b(read more|click here|learn more|see all|view all|details|more from|more articles|our story|about us|contact us|privacy|terms|login|signup|register)\b', title, re.I):
        return False
    if re.search(r'\b(tag|category|author|search|newsletter|blog|article|event|press|job|careers|team)\b', title, re.I):
        return False
    words = title.split()
    if len(words) > 5:
        return False
    capitalized = sum(1 for word in words if word[:1].isupper())
    if capitalized < max(1, len(words) // 2):
        return False
    return True


def fetch_html_list_items(page_url, max_items=20):
    response = requests.get(page_url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    items = []
    seen = set()
    container = soup.find('main') or soup

    for anchor in container.find_all('a', href=True):
        href = anchor['href'].strip()
        href = urljoin(page_url, href)
        title = anchor.get_text(strip=True)
        if not should_keep_html_link(page_url, href, title) or href in seen:
            continue
        seen.add(href)
        items.append({
            'title': title,
            'link': href,
            'description': 'Discovered from a logistics startup research page.',
            'published_at': '',
        })
        if len(items) >= max_items:
            break

    return items


def fetch_company_directory_items(page_url, max_items=20):
    response = requests.get(page_url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    items = []
    seen = set()
    container = soup.find('main') or soup

    for anchor in container.find_all('a', href=True):
        href = anchor['href'].strip()
        href = urljoin(page_url, href)
        title = anchor.get_text(strip=True)
        if href in seen:
            continue
        if not should_keep_html_link(page_url, href, title):
            continue
        if not looks_like_company_name(title):
            continue
        seen.add(href)
        items.append({
            'title': title,
            'link': href,
            'description': 'Company directory candidate from curated logistics research page.',
            'published_at': '',
        })
        if len(items) >= max_items:
            break

    return items


def get_or_create_source(source):
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
    }
    params = {'select': 'id', 'url': f'eq.{source["url"]}'}
    response = requests.get(
        f'{SUPABASE_REST_URL}/sources',
        headers=headers,
        params=params,
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if data:
        return data[0]['id']

    payload = {
        'type': source['type'],
        'url': source['url'],
        'active': True,
    }
    response = requests.post(
        f'{SUPABASE_REST_URL}/sources',
        headers={**headers, 'Content-Type': 'application/json', 'Prefer': 'return=representation'},
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    result = response.json()
    return result[0]['id'] if result else None


def save_raw_item(source_id, item):
    if not item.get('link'):
        return None

    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=representation',
    }
    payload = {
        'source_id': source_id,
        'url': item['link'],
        'title': item.get('title', ''),
        'content': item.get('description', ''),
        'published_at': item.get('published_at') or None,
        'processed': False,
    }
    response = requests.post(
        f'{SUPABASE_REST_URL}/raw_items?on_conflict=url',
        headers=headers,
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


if __name__ == '__main__':
    items = []
    source_ids = {}

    for source in SOURCES:
        print(f'Fetching source: {source["url"]}')
        try:
            source_id = get_or_create_source(source)
            source_ids[source['url']] = source_id
            if source['type'] == 'rss':
                for item in fetch_feed_items(source['url'], max_items=10):
                    item['source_url'] = source['url']
                    items.append(item)
            elif source['type'] == 'html':
                for item in fetch_html_list_items(source['url'], max_items=30):
                    item['source_url'] = source['url']
                    items.append(item)
        except Exception as exc:
            print(f'  Skipping source {source["url"]}: {exc}')

    directory_items = []
    for source in DIRECTORY_SOURCES:
        print(f'Fetching company directory source: {source["url"]}')
        try:
            if source['url'] not in source_ids:
                source_ids[source['url']] = get_or_create_source(source)
            for item in fetch_company_directory_items(source['url'], max_items=40):
                item['source_url'] = source['url']
                directory_items.append(item)
        except Exception as exc:
            print(f'  Skipping directory source {source["url"]}: {exc}')

    all_items = items + directory_items
    print(f'Collected {len(items)} discovery items and {len(directory_items)} directory candidates ({len(all_items)} total)')

    for item in items:
        try:
            source_id = source_ids.get(item.get('source_url'))
            if source_id:
                save_raw_item(source_id, item)
        except Exception as exc:
            print(f'  Warning: failed to save raw item for {item.get("link")}: {exc}')

    print('Discovery complete.')
