"""Publish the most recently emailed startup feature as a LinkedIn post.

Picks the company that notify_linkedin_feature.py emailed last
(linkedin_featured_at set) and that has not been posted yet
(linkedin_posted_at is null), publishes the same draft text to the
personal profile and marks it as posted.

Configuration:
  SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY
  LINKEDIN_ACCESS_TOKEN  – OAuth token with w_member_social (+ openid/profile)
  LINKEDIN_PERSON_ID     – optional; looked up via /v2/userinfo if not set
  LINKEDIN_API_VERSION   – optional, YYYYMM (default 202506)
"""
import os
import re
import sys
from datetime import datetime, timezone

import requests

from linkedin_card import render_card
from notify_linkedin_feature import SUPABASE_REST_URL, _headers, build_linkedin_draft

API_VERSION = os.getenv('LINKEDIN_API_VERSION', '202506')
# LinkedIn "little text" reserves these characters; '#' stays unescaped for hashtags.
_RESERVED = re.compile(r'([\\|{}@\[\]()<>*_~])')


def escape_commentary(text):
    return _RESERVED.sub(r'\\\1', text)


def pick_company():
    response = requests.get(
        f'{SUPABASE_REST_URL}/companies',
        headers=_headers(),
        params={
            'select': 'id,name,domain,description,category,country,hq_city,funding_stage,website',
            'linkedin_featured_at': 'not.is.null',
            'linkedin_posted_at': 'is.null',
            'order': 'linkedin_featured_at.desc',
            'limit': '1',
        },
        timeout=20,
    )
    response.raise_for_status()
    rows = response.json()
    return rows[0] if rows else None


def person_urn(token):
    person_id = os.getenv('LINKEDIN_PERSON_ID')
    if not person_id:
        response = requests.get(
            'https://api.linkedin.com/v2/userinfo',
            headers={'Authorization': f'Bearer {token}'},
            timeout=20,
        )
        response.raise_for_status()
        person_id = response.json()['sub']
    return f'urn:li:person:{person_id}'


def upload_image(token, author, png_bytes):
    headers = {
        'Authorization': f'Bearer {token}',
        'LinkedIn-Version': API_VERSION,
        'X-Restli-Protocol-Version': '2.0.0',
    }
    init = requests.post(
        'https://api.linkedin.com/rest/images?action=initializeUpload',
        headers=headers,
        json={'initializeUploadRequest': {'owner': author}},
        timeout=30,
    )
    if not init.ok:
        raise RuntimeError(f'LinkedIn image init error {init.status_code}: {init.text}')
    value = init.json()['value']
    upload = requests.put(
        value['uploadUrl'],
        headers={'Authorization': f'Bearer {token}'},
        data=png_bytes,
        timeout=60,
    )
    upload.raise_for_status()
    return value['image']


def publish(token, author, text, image_urn=None, image_alt=''):
    body = {
        'author': author,
        'commentary': escape_commentary(text),
        'visibility': 'PUBLIC',
        'distribution': {
            'feedDistribution': 'MAIN_FEED',
            'targetEntities': [],
            'thirdPartyDistributionChannels': [],
        },
        'lifecycleState': 'PUBLISHED',
        'isReshareDisabledByAuthor': False,
    }
    if image_urn:
        body['content'] = {'media': {'id': image_urn, 'altText': image_alt}}
    response = requests.post(
        'https://api.linkedin.com/rest/posts',
        headers={
            'Authorization': f'Bearer {token}',
            'LinkedIn-Version': API_VERSION,
            'X-Restli-Protocol-Version': '2.0.0',
            'Content-Type': 'application/json',
        },
        json=body,
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f'LinkedIn API error {response.status_code}: {response.text}')
    return response.headers.get('x-restli-id', '')


def mark_posted(company_id):
    response = requests.patch(
        f'{SUPABASE_REST_URL}/companies?id=eq.{company_id}',
        headers={**_headers(), 'Content-Type': 'application/json'},
        json={'linkedin_posted_at': datetime.now(timezone.utc).isoformat()},
        timeout=20,
    )
    response.raise_for_status()


def main():
    token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not token:
        sys.exit('LINKEDIN_ACCESS_TOKEN is not set.')

    company = pick_company()
    if not company:
        print('Nothing to post: no emailed feature without a LinkedIn post.')
        return

    author = person_urn(token)
    image_urn = upload_image(token, author, render_card(company))
    post_id = publish(
        token, author, build_linkedin_draft(company), image_urn, f"Startup spotlight: {company['name']}"
    )
    mark_posted(company['id'])
    print(f"Posted {company['name']} to LinkedIn ({post_id}).")


if __name__ == '__main__':
    main()
