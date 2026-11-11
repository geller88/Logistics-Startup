"""Render a 1200x627 spotlight card image for a LinkedIn post."""
import io
import textwrap

import requests
from PIL import Image, ImageDraw, ImageFont

BG = '#f4efe4'
DARK = '#3b2f24'
TAN = '#d9b98a'
BOLD_FONTS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
]
REGULAR_FONTS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/System/Library/Fonts/Supplemental/Arial.ttf',
]


def _font(paths, size):
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _logo(domain):
    if not domain:
        return None
    try:
        response = requests.get(
            'https://www.google.com/s2/favicons', params={'domain': domain, 'sz': 128}, timeout=15
        )
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert('RGBA').resize((128, 128))
    except Exception:
        return None


def render_card(company):
    """Return PNG bytes for the company's spotlight card."""
    image = Image.new('RGB', (1200, 627), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, 1200, 20], fill=DARK)
    draw.rectangle([0, 607, 1200, 627], fill=DARK)

    draw.text((70, 70), 'STARTUP SPOTLIGHT', font=_font(BOLD_FONTS, 28), fill=TAN)
    category = (company.get('category') or 'Logistics').upper()
    draw.text((70, 112), category, font=_font(BOLD_FONTS, 30), fill=DARK)

    logo = _logo(company.get('domain'))
    name_x = 70
    if logo:
        tile = Image.new('RGB', (160, 160), 'white')
        tile.paste(logo, (16, 16), logo)
        image.paste(tile, (70, 200))
        name_x = 262

    name = company.get('name') or 'Unknown'
    name_font = _font(BOLD_FONTS, 84 if len(name) <= 16 else 60)
    draw.text((name_x, 220), name, font=name_font, fill=DARK)
    location = ', '.join(filter(None, [company.get('hq_city'), company.get('country')]))
    if location:
        draw.text((name_x, 330), location, font=_font(REGULAR_FONTS, 36), fill=DARK)

    description = company.get('description') or ''
    if len(description) > 170:
        description = description[:167].rsplit(' ', 1)[0] + '...'
    y = 420
    for line in textwrap.wrap(description, width=62)[:3]:
        draw.text((70, y), line, font=_font(REGULAR_FONTS, 30), fill=DARK)
        y += 44

    draw.text((70, 560), 'Logistics Startup Monitor', font=_font(BOLD_FONTS, 26), fill=TAN)

    buffer = io.BytesIO()
    image.save(buffer, 'PNG')
    return buffer.getvalue()
