import os
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

PROMPT = '''
Extract a structured profile from the following company description.
Return JSON with fields: name, domain, website, description, founding_year, country, hq_city, funding_stage, categories, focus.
If a field is missing, return an empty string or empty list.

Text:
"""
{content}
"""
'''


def enrich_text(content):
    response = openai.ChatCompletion.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'user', 'content': PROMPT.format(content=content)}
        ],
        max_tokens=300,
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()


if __name__ == '__main__':
    sample = 'Schnelle Lieferung für E-Commerce mit autonomen Lagerrobotern und Tracking Software, gegründet 2023 in München.'
    print(enrich_text(sample))
