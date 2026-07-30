import { NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabaseServerClient';

export async function POST(request) {
  const { query } = await request.json();
  if (!query || query.trim().length === 0) {
    return NextResponse.json({ error: 'Query is required.' }, { status: 400 });
  }

  const q = query.trim();
  const normalized = q.replace(/\s+/g, ' ').toLowerCase();
  const terms = normalized.split(' ').map((term) => term.trim()).filter(Boolean);
  let filters = `name.ilike.%${normalized}%,website.ilike.%${normalized}%,description.ilike.%${normalized}%,country.ilike.%${normalized}%,hq_city.ilike.%${normalized}%`;

  if (terms.length > 1) {
    filters += `,domain.ilike.%${normalized}%`;
  }

  const { data, error } = await supabaseServer
    .from('companies')
    .select('id, name, website, country, hq_city, funding_stage, status, description')
    .or(filters)
    .order('created_at', { ascending: false })
    .limit(50);

  if (error) {
    return NextResponse.json({ error: error.message, hint: error.hint || null }, { status: 500 });
  }

  return NextResponse.json({ results: data });
}
