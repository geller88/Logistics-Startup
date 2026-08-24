"""Email notification: pick one new logistics startup to feature on LinkedIn.

Picks the most recently discovered "interesting" company that hasn't been
featured yet (excluding bankrupt/shut-down ones), emails a short LinkedIn-ready
write-up, and marks it as featured so it won't be picked again.

Configuration via .env (same convention as other projects' email senders):
  SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY  – already required by the pipeline
  EMAIL_SENDER      – sender address (e.g. your Gmail)
  EMAIL_PASSWORD    – app password (Gmail: Account settings -> Security -> App passwords)
  EMAIL_RECIPIENT   – who receives the notification
  EMAIL_SMTP_HOST   – SMTP server (default: smtp.gmail.com)
  EMAIL_SMTP_PORT   – SMTP port (default: 587)

Run manually:
    python notify_linkedin_feature.py
"""
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent
load_dotenv(base_dir / '.env')
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError('Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your environment or .env file.')

SUPABASE_REST_URL = f'{SUPABASE_URL}/rest/v1'
HIDDEN_STATUS_PATTERNS = ['*bankrupt*', '*shut down*', '*shut_down*']


def _headers():
    return {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
    }


def pick_unfeatured_company():
    """Return the most recently discovered, not-yet-featured interesting company, or None."""
    params = {
        'select': 'id,name,domain,website,description,category,country,hq_city,funding_stage',
        'interesting': 'eq.true',
        'linkedin_featured_at': 'is.null',
        'order': 'created_at.desc',
        'limit': '1',
    }
    response = requests.get(
        f'{SUPABASE_REST_URL}/companies',
        headers=_headers(),
        params=[
            *params.items(),
            *[('status', f'not.ilike.{p}') for p in HIDDEN_STATUS_PATTERNS],
        ],
        timeout=20,
    )
    response.raise_for_status()
    rows = response.json()
    return rows[0] if rows else None


def mark_as_featured(company_id):
    response = requests.patch(
        f'{SUPABASE_REST_URL}/companies?id=eq.{company_id}',
        headers={**_headers(), 'Content-Type': 'application/json'},
        json={'linkedin_featured_at': datetime.now(timezone.utc).isoformat()},
        timeout=20,
    )
    response.raise_for_status()


def build_email_html(company):
    name = company.get('name', 'Unknown')
    description = company.get('description') or ''
    category = company.get('category') or 'Other'
    country = company.get('country') or ''
    hq_city = company.get('hq_city') or ''
    funding_stage = company.get('funding_stage') or ''
    website = company.get('website') or ''
    location = ', '.join(filter(None, [hq_city, country])) or 'Location unknown'

    linkedin_draft = (
        f"Spotlight: {name} ({category})\n\n"
        f"{description}\n\n"
        f"📍 {location}"
        + (f" · {funding_stage}" if funding_stage else '')
        + (f"\n🔗 {website}" if website else '')
        + "\n\n#LogisticsInnovation #SupplyChain #StartupSpotlight"
    )

    return f"""
    <div style="font-family: sans-serif; max-width: 600px;">
      <h2>This week's LinkedIn feature: {name}</h2>
      <p><strong>Category:</strong> {category}<br>
         <strong>Location:</strong> {location}<br>
         {'<strong>Funding:</strong> ' + funding_stage + '<br>' if funding_stage else ''}
         {'<strong>Website:</strong> <a href="' + website + '">' + website + '</a><br>' if website else ''}</p>
      <p>{description}</p>
      <h3>Suggested LinkedIn post</h3>
      <pre style="white-space: pre-wrap; background: #f4efe4; padding: 16px; border-radius: 8px; font-family: sans-serif;">{linkedin_draft}</pre>
    </div>
    """


def send_email(company):
    sender = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')
    recipient = os.getenv('EMAIL_RECIPIENT')

    if not all([sender, password, recipient]):
        print('Email not configured (EMAIL_SENDER/PASSWORD/RECIPIENT missing) — skipping send.')
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🚚 LinkedIn feature idea: {company.get('name', 'New startup')}"
    msg['From'] = f'Logistics Startup Market <{sender}>'
    msg['To'] = recipient
    msg.attach(MIMEText(build_email_html(company), 'html', 'utf-8'))

    smtp_host = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        print(f"Email sent: featuring {company.get('name')} -> {recipient}")
        return True
    except smtplib.SMTPAuthenticationError:
        print('Email: authentication failed — check the app password.')
    except smtplib.SMTPException as exc:
        print(f'Email SMTP error: {exc}')
    except OSError as exc:
        print(f'Email network error: {exc}')
    return False


def notify_new_startup_for_linkedin():
    """Pick one unfeatured startup, email it, and mark it as featured. Returns the company or None."""
    company = pick_unfeatured_company()
    if not company:
        print('No unfeatured interesting startups available.')
        return None

    if send_email(company):
        mark_as_featured(company['id'])

    return company


if __name__ == '__main__':
    notify_new_startup_for_linkedin()
