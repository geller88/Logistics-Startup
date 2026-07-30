import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import openai
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent
load_dotenv(base_dir / '.env')
load_dotenv()

try:
    import migrate_schema
except ImportError:
    migrate_schema = None

SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_API_URL = os.getenv('ANTHROPIC_API_URL', 'https://api.anthropic.com')
ANTHROPIC_COMPLETION_MODEL = os.getenv('ANTHROPIC_COMPLETION_MODEL', 'claude-sonnet-5')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError('Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your environment or .env file.')
if SUPABASE_SERVICE_ROLE_KEY.startswith('sb_publishable_'):
    raise RuntimeError('SUPABASE_SERVICE_ROLE_KEY must be the Supabase service role key, not a publishable anon key.')
if not OPENAI_API_KEY and not ANTHROPIC_API_KEY:
    raise RuntimeError('Set OPENAI_API_KEY or ANTHROPIC_API_KEY in your environment or .env file.')

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
SUPABASE_REST_URL = f'{SUPABASE_URL}/rest/v1'

SOURCES = [
    {'type': 'html', 'url': 'https://techcrunch.com/tag/logistics/'},
    {'type': 'html', 'url': 'https://techcrunch.com/tag/supply-chain/'},
    {'type': 'html', 'url': 'https://www.eu-startups.com/tag/logistics/'},
    {'type': 'html', 'url': 'https://tech.eu/'},
    {'type': 'rss', 'url': 'https://www.freightwaves.com/feed/'},
    {'type': 'rss', 'url': 'https://www.supplychaindive.com/feeds/news/'},
    {'type': 'rss', 'url': 'https://feeds.feedburner.com/logisticsmgmt/latest'},
    {'type': 'rss', 'url': 'https://theloadstar.com/feed/'},
    {'type': 'rss', 'url': 'https://www.rfidjournal.com/feed'},
]

HEADERS = {
    'User-Agent': 'logistics-startup-market-loader/1.0 (+https://example.com)',
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
        items.append({'title': title, 'link': link, 'description': description, 'published_at': pub_date})

    return items


def should_keep_html_link(page_url, href, title):
    if not href or href.startswith('#') or href.startswith('mailto:') or href.startswith('javascript:'):
        return False
    title = title.strip()
    if len(title) < 4 or len(title) > 120:
        return False
    if re.search(r'\b(read more|click here|learn more|privacy policy|terms of use|contact us|cookies|login|subscribe|newsletter|signup|register|advertise|our team)\b', title, re.I):
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


def guess_domain(url):
    try:
        host = urlparse(url).hostname or ''
        return host.replace('www.', '')
    except Exception:
        return ''


DOMAIN_RE = re.compile(r'^(?!-)[a-z0-9-]{1,63}(?<!-)(\.[a-z0-9-]{1,63}(?<!-))+$', re.I)


def looks_like_domain(value):
    value = (value or '').strip().lower()
    if not value or ' ' in value or '/' in value:
        return False
    return bool(DOMAIN_RE.match(value))


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('true', '1', 'yes', 'y')
    return False


CATEGORIES = [
    ('Transport & Freight', 'TRA'),
    ('Warehousing & Fulfillment', 'WHF'),
    ('Tracking & Visibility', 'TRV'),
    ('Labeling & Packaging', 'LAB'),
    ('Digital Freight & Marketplaces', 'DFM'),
    ('Supply Chain Software & Analytics', 'SCA'),
    ('Customs, Compliance & Trade', 'CCT'),
    ('Sustainability & Green Logistics', 'SGL'),
]
CATEGORY_NAMES = [name for name, _code in CATEGORIES]


def normalize_category(value):
    value = (value or '').strip()
    for name, code in CATEGORIES:
        if value.lower() == name.lower() or value.lower() == code.lower():
            return name
    return 'Other'


def normalize_profile(profile, item):
    raw_domain = (profile.get('domain') or '').strip()
    domain = raw_domain if looks_like_domain(raw_domain) else ''
    if not domain:
        domain = guess_domain(profile.get('website', '') or '')
    if not domain:
        domain = guess_domain(item['link'])
    website = profile.get('website', '') or item['link']
    name = profile.get('name', '') or item['title'] or domain

    return {
        'name': name,
        'domain': domain,
        'website': website,
        'description': profile.get('description', '') or item['description'] or '',
        'founding_year': profile.get('founding_year') or None,
        'country': profile.get('country', ''),
        'hq_city': profile.get('hq_city', ''),
        'funding_stage': profile.get('funding_stage', ''),
        'status': profile.get('status', 'active') or 'active',
        'interesting': parse_bool(profile.get('interesting', False)),
        'product_status': profile.get('product_status', ''),
        'product_timeline': profile.get('product_timeline', ''),
        'has_product': parse_bool(profile.get('has_product', False)),
        'category': normalize_category(profile.get('category')),
    }


def anthropic_complete(prompt):
    headers = {
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': os.getenv('ANTHROPIC_VERSION', '2023-06-01'),
        'Content-Type': 'application/json',
    }
    payload = {
        'model': ANTHROPIC_COMPLETION_MODEL,
        'messages': [
            {'role': 'user', 'content': prompt},
        ],
        'max_tokens': 300,
    }
    response = requests.post(f'{ANTHROPIC_API_URL}/v1/messages', headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    if isinstance(data.get('content'), list):
        texts = [item.get('text', '') for item in data['content'] if item.get('type') == 'text']
        return ''.join(texts).strip()
    return data.get('completion') or data.get('completion_text') or data.get('output') or ''


def extract_json_object(text):
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
        text = re.sub(r'```$', '', text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{.*\}', text, re.S)
    if match:
        return json.loads(match.group(0))
    raise json.JSONDecodeError('No JSON object found', text, 0)


def enrich_item_with_anthropic(item):
    prompt = f"""Extract a structured logistics startup profile from the following text. Respond with a single JSON object and nothing else — no markdown, no code fences, no commentary.

Text:
{item['title']}
{item['description']}

URL: {item['link']}

The JSON object must contain these fields:
- name (the company's proper name, not the article headline)
- domain (the company's website internet domain, e.g. "example.com" — this must be an actual domain name, NEVER an industry/category/business description; leave it as an empty string if you cannot determine the company's real website domain)
- website (the full company website URL if known, e.g. "https://example.com")
- description
- founding_year
- country
- hq_city
- funding_stage
- status
- interesting
- has_product
- product_status
- product_timeline
- category (must be exactly one of these 8 names — pick the single best fit:
  "Transport & Freight" — companies that physically move goods: trucking, shipping lines, airlines/cargo, rail, last-mile delivery execution, ports/terminals.
  "Warehousing & Fulfillment" — warehouse robotics, fulfillment centers, storage, inventory management, industrial/logistics real estate.
  "Tracking & Visibility" — real-time shipment tracking, IoT sensors, condition/location monitoring, supply chain visibility platforms.
  "Labeling & Packaging" — shipping labels, packaging design/materials, print-and-apply systems, and smart/connected labeling technology (RFID, NFC, smart tags, digital product passports).
  "Digital Freight & Marketplaces" — online freight forwarding platforms, load-matching marketplaces, digital freight brokers connecting shippers and carriers.
  "Supply Chain Software & Analytics" — TMS/WMS/ERP software, planning and forecasting tools, data analytics for supply chain operations (not primarily a marketplace or tracking-hardware company).
  "Customs, Compliance & Trade" — customs brokerage, trade compliance, cross-border documentation, tariff/duty management.
  "Sustainability & Green Logistics" — decarbonization, electric/alternative-fuel fleets, emissions reduction, green cold chain.
  If none clearly fit, return "Other".)

Return `interesting` as `true` only when this is an actual startup or scale-up (privately held, still building product/market fit or early growth) worth monitoring for traction or innovation in logistics operations. Return `false` for large public companies, multinational incumbents, government/industry bodies, or any organization that is not itself a startup — even if the article is about logistics.

Set `has_product` to `true` when the company appears to have an actual product, platform, or live service; otherwise `false`.

If a field is unknown, return an empty string, and use `false` for boolean fields.
"""
    text = anthropic_complete(prompt)
    try:
        profile = extract_json_object(text)
    except json.JSONDecodeError:
        return None
    return normalize_profile(profile, item)


def enrich_item_with_openai(item):
    prompt = f"""
Extract a structured logistics startup profile from the following text. Return valid JSON only.

Text:
{item['title']}
{item['description']}

URL: {item['link']}

Respond with JSON object containing these fields:
- name (the company's proper name, not the article headline)
- domain (the company's website internet domain, e.g. "example.com" — this must be an actual domain name, NEVER an industry/category/business description; leave it as an empty string if you cannot determine the company's real website domain)
- website (the full company website URL if known, e.g. "https://example.com")
- description
- founding_year
- country
- hq_city
- funding_stage
- status
- interesting
- has_product
- product_status
- product_timeline
- category (must be exactly one of these 8 names — pick the single best fit:
  "Transport & Freight" — companies that physically move goods: trucking, shipping lines, airlines/cargo, rail, last-mile delivery execution, ports/terminals.
  "Warehousing & Fulfillment" — warehouse robotics, fulfillment centers, storage, inventory management, industrial/logistics real estate.
  "Tracking & Visibility" — real-time shipment tracking, IoT sensors, condition/location monitoring, supply chain visibility platforms.
  "Labeling & Packaging" — shipping labels, packaging design/materials, print-and-apply systems, and smart/connected labeling technology (RFID, NFC, smart tags, digital product passports).
  "Digital Freight & Marketplaces" — online freight forwarding platforms, load-matching marketplaces, digital freight brokers connecting shippers and carriers.
  "Supply Chain Software & Analytics" — TMS/WMS/ERP software, planning and forecasting tools, data analytics for supply chain operations (not primarily a marketplace or tracking-hardware company).
  "Customs, Compliance & Trade" — customs brokerage, trade compliance, cross-border documentation, tariff/duty management.
  "Sustainability & Green Logistics" — decarbonization, electric/alternative-fuel fleets, emissions reduction, green cold chain.
  If none clearly fit, return "Other".)

Return `interesting` as `true` only when this is an actual startup or scale-up (privately held, still building product/market fit or early growth) worth monitoring for traction or innovation in logistics operations. Return `false` for large public companies, multinational incumbents, government/industry bodies, or any organization that is not itself a startup — even if the article is about logistics.

Set `has_product` to `true` when the company appears to have an actual product, platform, or live service; otherwise `false`.

If a field is unknown, return an empty string, and use `false` for boolean fields.
"""

    response = openai.ChatCompletion.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': 'You are a data extraction assistant.'},
            {'role': 'user', 'content': prompt},
        ],
        max_tokens=300,
        temperature=0.0,
    )

    text = response.choices[0].message.content
    try:
        profile = extract_json_object(text)
    except json.JSONDecodeError:
        return None

    return normalize_profile(profile, item)


def enrich_item_with_llm(item):
    if OPENAI_API_KEY:
        return enrich_item_with_openai(item)
    return enrich_item_with_anthropic(item)


def generate_profile_embedding(profile):
    text = profile.get('description') or profile.get('name') or ''
    if not text:
        return None

    if OPENAI_API_KEY:
        response = openai.Embedding.create(
            model='text-embedding-3-small',
            input=text,
        )
        return response.data[0].embedding

    print('No OPENAI_API_KEY configured; skipping profile embeddings for now.')
    return None


def get_existing_domains():
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
    }
    response = requests.get(
        f'{SUPABASE_REST_URL}/companies?select=domain',
        headers=headers,
        timeout=20,
    )
    response.raise_for_status()
    return {entry['domain'] for entry in response.json() if entry.get('domain')}


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


def resolve_seedtable_website(page_url):
    if 'seedtable.com' not in page_url:
        return page_url

    try:
        response = requests.get(page_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for anchor in soup.find_all('a', href=True):
            href = anchor['href'].strip()
            if not href or href.startswith('#'):
                continue
            href = urljoin(page_url, href)
            host = urlparse(href).hostname or ''
            if host and 'seedtable.com' not in host:
                return href
    except Exception:
        pass

    return page_url


def scrape_website_product_signals(website_url):
    if not website_url:
        return {
            'product_status': '',
            'product_timeline': '',
            'has_product': False,
        }

    try:
        response = requests.get(website_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = ' '.join(soup.stripped_strings)
    except Exception:
        return {
            'product_status': '',
            'product_timeline': '',
            'has_product': False,
        }

    if not text:
        return {
            'product_status': '',
            'product_timeline': '',
            'has_product': False,
        }

    product_terms = re.compile(r'\b(product|platform|app|service|software|solution|technology|logistics)\b', re.I)
    launch_terms = re.compile(r'\b(launched|available|now shipping|now available|release|released|live|customer|users?|beta|pilot|coming soon|early access)\b', re.I)
    prelaunch_terms = re.compile(r'\b(beta|pilot|coming soon|early access|pre-launch|prototype|waiting list|launching soon)\b', re.I)

    has_product = bool(product_terms.search(text))
    if launch_terms.search(text) and has_product:
        product_status = 'live product'
    elif prelaunch_terms.search(text) and has_product:
        product_status = 'early-stage / pre-launch'
    elif has_product:
        product_status = 'product presence detected'
    else:
        product_status = ''

    timeline_sentences = []
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        if len(timeline_sentences) >= 3:
            break
        if re.search(r'\b(launch(?:ed|es|ing)?|released|beta|pilot|coming soon|early access|available|since|founded|established)\b', sentence, re.I):
            timeline_sentences.append(sentence.strip())

    product_timeline = ' '.join(timeline_sentences).strip()

    return {
        'product_status': product_status,
        'product_timeline': product_timeline,
        'has_product': has_product,
    }


def insert_company(company):
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=representation',
    }
    response = requests.post(
        f'{SUPABASE_REST_URL}/companies?on_conflict=domain',
        headers=headers,
        json=company,
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(f'Insert failed: {response.status_code} {response.text}')
    return response.json()


def main():
    print('Loading logistics startup candidates from discovery sources...')
    if migrate_schema is not None:
        migrate_schema.apply_schema_migration()
    existing_domains = get_existing_domains()
    print(f'Found {len(existing_domains)} existing companies by domain.')
    publisher_domains = {guess_domain(source['url']) for source in SOURCES}

    items = []
    source_ids = {}
    for source in SOURCES:
        print(f'Fetching source: {source["url"]}')
        try:
            source_id = get_or_create_source(source)
            if source['type'] == 'rss':
                for item in fetch_feed_items(source['url'], max_items=25):
                    item['source_url'] = source['url']
                    items.append(item)
            elif source['type'] == 'html':
                for item in fetch_html_list_items(source['url'], max_items=40):
                    item['source_url'] = source['url']
                    items.append(item)
            else:
                print(f'  Unknown source type: {source["type"]}, skipping.')
                continue
            source_ids[source['url']] = source_id
        except Exception as exc:
            print(f'  Skipping source {source["url"]}: {exc}')

    print(f'Collected {len(items)} discovery items.')

    inserted = 0
    skipped = 0

    for item in items:
        if not item['link']:
            skipped += 1
            continue

        source_id = source_ids.get(item.get('source_url'))
        try:
            if source_id:
                save_raw_item(source_id, item)
        except Exception as exc:
            print(f'  Warning: failed to save raw item: {exc}')

        print(f'Enriching item: {item["title"][:70]}')
        profile = enrich_item_with_llm(item)
        if profile is None:
            print('  Skipping: could not extract a structured profile.')
            skipped += 1
            continue
        if not profile['domain'] or profile['domain'] in publisher_domains:
            print(f'  Skipping: no identifiable company domain (got "{profile["domain"]}").')
            skipped += 1
            continue
        if profile['domain'] in existing_domains:
            print(f'Already exists: {profile["domain"]}')
            skipped += 1
            continue

        company_website = resolve_seedtable_website(profile.get('website') or item['link'])
        signals = scrape_website_product_signals(company_website)
        profile.update(signals)

        embedding = generate_profile_embedding(profile)
        if embedding is not None:
            profile['profile_embedding'] = embedding

        try:
            inserted_rows = insert_company(profile)
            if inserted_rows:
                print(f'Inserted company: {profile["name"]} ({profile["domain"]})')
                inserted += 1
                existing_domains.add(profile['domain'])
        except Exception as exc:
            print(f'Failed to insert company {profile["name"]}: {exc}')
            skipped += 1

    print(f'Inserted {inserted} new companies, skipped {skipped} items.')


if __name__ == '__main__':
    main()
