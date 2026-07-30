import { NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabaseServerClient';

const SELECT_FIELDS = 'id, name, website, country, hq_city, funding_stage, status, description, interesting, category';
const HIDDEN_STATUSES = ['%bankrupt%', '%shut down%', '%shut_down%'];

function excludeHiddenStatuses(query) {
  return HIDDEN_STATUSES.reduce((q, pattern) => q.not('status', 'ilike', pattern), query);
}

export async function GET() {
  const { data, error } = await excludeHiddenStatuses(
    supabaseServer
      .from('companies')
      .select(SELECT_FIELDS)
      .eq('interesting', true)
  )
    .order('created_at', { ascending: false })
    .limit(50);

  if (error) {
    return NextResponse.json({ error: error.message, hint: error.hint || null }, { status: 500 });
  }

  if (!data || data.length === 0) {
    const fallback = await excludeHiddenStatuses(
      supabaseServer.from('companies').select(SELECT_FIELDS)
    )
      .order('created_at', { ascending: false })
      .limit(50);

    if (fallback.error) {
      return NextResponse.json({ error: fallback.error.message, hint: fallback.error.hint || null }, { status: 500 });
    }

    return NextResponse.json({ companies: fallback.data, fallback: true });
  }

  return NextResponse.json({ companies: data });
}
