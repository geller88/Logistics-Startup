import os
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


def embed_text(text):
    response = openai.Embedding.create(
        model='text-embedding-3-small',
        input=text,
    )
    return response.data[0].embedding


if __name__ == '__main__':
    print(embed_text('Logistics startup tracking system with product updates and market intelligence.'))
