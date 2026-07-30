# Logistics Startup Market

This is the foundation for a logistics innovation tracker in MVP format.
It is built with a modular architecture including a discovery pipeline, a Supabase database, and a web app.

## Project structure

- `pipeline/` — daily discovery, dedupe, enrichment, and embedding pipeline.
- `supabase/` — database schema and Postgres/pgvector definitions.
- `web/` — Next.js frontend for marketplace, company profiles, search, and follow/watchlist features.
- `public/` — optional legacy frontend, currently a placeholder.

## Architecture overview

1. **Discovery**
   - RSS/news sources, Product Hunt, accelerator lists, Google News.
   - New URLs and raw items land in `raw_items`.
2. **Dedupe + Enrichment**
   - Raw items are structured with Claude Haiku.
   - Known companies get update timelines; new companies are created as candidates.
3. **Tracking**
   - Updates are stored and later combined into digests.
   - Followed companies generate personalized watchlists.
4. **Search**
   - Structured filtering by category and location.
   - LLM-powered RAG search over profiles + updates.

## Run locally

### Pipeline
```bash
cd "/Users/geller/Documents/AI/Logistics Startup market/pipeline"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Web app
```bash
cd "/Users/geller/Documents/AI/Logistics Startup market/web"
npm install
npm run dev
```

## Next steps

- Create a Supabase project and apply the schema from `supabase/schema.sql`.
- Set up GitHub Actions for daily pipeline jobs.
- Expand the Next.js web app with user login, startup monitoring, and LLM search.

## Pipeline automation

The repository now includes a daily pipeline workflow at `.github/workflows/pipeline-load.yml`.
It runs `pipeline/load_companies.py` on a schedule and via manual dispatch.

### Required repository secrets

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`

### Local pipeline command

```bash
cd pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python load_companies.py
```

### Local pipeline environment file

Create a local `.env` file in `pipeline/` to keep secrets off source control:

```bash
cp pipeline/.env.example pipeline/.env
```

Set your keys in `pipeline/.env`.
- Use `OPENAI_API_KEY` if you have OpenAI access.
- Use `ANTHROPIC_API_KEY` if you have a Claude key.
- `SUPABASE_SERVICE_ROLE_KEY` must be a Supabase service role key, not a publishable anon key.

Example (`pipeline/.env`):

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
ANTHROPIC_API_KEY=your-claude-key
```

The loader will read `pipeline/.env` automatically when run from either the repository root or the `pipeline/` directory.

### Optional schema migration

If you set `SUPABASE_DATABASE_URL` or `DATABASE_URL`, the pipeline will apply `supabase/schema.sql` automatically before loading companies.

```bash
export SUPABASE_DATABASE_URL="your-postgres-connection-string"
python load_companies.py
```
### What is loaded

The pipeline loader now:
- discovers logistics startup content from RSS feeds
- enriches each company with OpenAI
- generates `profile_embedding` vectors
- inserts companies into Supabase with `profile_embedding`
