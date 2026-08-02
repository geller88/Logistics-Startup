"""Manually add a single known company that discovery feeds won't surface.

RSS/HTML discovery only ever sees the most recent ~25-40 items per source, so a
real company with no very recent press (funding round from a while back, no
news hits this week, etc.) will never be picked up no matter how many sources
are added. Use this script to insert it directly once you've verified the facts
yourself (e.g. via a web search) — it reuses the same normalization, dedup, and
embedding logic as the discovery pipeline.

Example:
    python add_company.py --name Paxafe --domain paxafe.com \\
        --website https://paxafe.com \\
        --description "Paxafe provides an AI-driven cold chain risk intelligence platform (CONTXT) that predicts adverse supply chain events for pharma, food, and perishables shipments." \\
        --country "United States" --hq-city Indianapolis \\
        --founding-year 2018 --funding-stage "Series A" \\
        --category "Tracking & Visibility"
"""
import argparse

from load_companies import CATEGORY_NAMES, generate_profile_embedding, insert_company, normalize_profile


def add_company(name, domain, website, description, country='', hq_city='', address='', zip_code='',
                 phone='', founding_year=None, funding_stage='', status='active', category='Other',
                 interesting=True, has_product=True, product_status='', product_timeline=''):
    item = {'title': name, 'description': description, 'link': website or f'https://{domain}'}
    raw_profile = {
        'name': name,
        'domain': domain,
        'website': website or f'https://{domain}',
        'description': description,
        'founding_year': founding_year,
        'country': country,
        'hq_city': hq_city,
        'address': address,
        'zip_code': zip_code,
        'phone': phone,
        'funding_stage': funding_stage,
        'status': status,
        'interesting': interesting,
        'has_product': has_product,
        'product_status': product_status,
        'product_timeline': product_timeline,
        'category': category,
    }
    profile = normalize_profile(raw_profile, item)

    embedding = generate_profile_embedding(profile)
    if embedding is not None:
        profile['profile_embedding'] = embedding

    return insert_company(profile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--name', required=True)
    parser.add_argument('--domain', required=True, help='e.g. paxafe.com (no protocol)')
    parser.add_argument('--website', default='', help='defaults to https://<domain>')
    parser.add_argument('--description', required=True)
    parser.add_argument('--country', default='')
    parser.add_argument('--hq-city', default='')
    parser.add_argument('--address', default='')
    parser.add_argument('--zip-code', default='')
    parser.add_argument('--phone', default='')
    parser.add_argument('--founding-year', type=int, default=None)
    parser.add_argument('--funding-stage', default='')
    parser.add_argument('--status', default='active')
    parser.add_argument('--category', default='Other', choices=CATEGORY_NAMES + ['Other'])
    parser.add_argument('--not-interesting', action='store_true', help='mark as not a startup worth surfacing publicly')
    parser.add_argument('--no-product', action='store_true', help='mark as not yet having a live product')
    args = parser.parse_args()

    result = add_company(
        name=args.name,
        domain=args.domain,
        website=args.website,
        description=args.description,
        country=args.country,
        hq_city=args.hq_city,
        address=args.address,
        zip_code=args.zip_code,
        phone=args.phone,
        founding_year=args.founding_year,
        funding_stage=args.funding_stage,
        status=args.status,
        category=args.category,
        interesting=not args.not_interesting,
        has_product=not args.no_product,
    )
    print('Result:', result)
