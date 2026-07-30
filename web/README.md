# Logistics Startup Market Web

Next.js frontend for the Logistics Startup Market MVP.

## Setup

1. `cd "/Users/geller/Documents/AI/Logistics Startup market/web"`
2. `npm install`
3. `npm run dev`

## Supabase

Required environment variables:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_URL`

## Endpoints

- `GET /api/companies` — returns the first 50 company profiles
- `POST /api/search` — simple text search across name, website, description, country, and city

## Pages

- `/` — redesigned homepage with logistics category cards and product story
- `/companies` — startup monitor list with free registration gating for details
- `/search` — discovery search over company data without paid LLM calls
- `/auth` — free registration and sign-in flow
- `/premium` — premium research concept page for paid logistics analysis
- `/admin/requests` — admin review page for premium research requests

## Premium research request

- `POST /api/premium` — submit a premium research request for logged-in users
- `GET /api/admin/requests` — returns premium requests for authorized admin emails

## Admin access

Set `ADMIN_EMAILS` in `.env.local` to a comma-separated list of admin user emails. The admin review page only works for signed-in users with an allowed email.

> Note: API routes now use the Supabase service role key on the server side, so your anon key only needs public access for other client-side features.

## Extensions

- `search` can later be switched to pgvector/RAG.
- `companies` can be extended with filtering and pagination.
