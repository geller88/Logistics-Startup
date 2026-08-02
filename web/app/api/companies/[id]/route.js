import { NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabaseServerClient';

const SELECT_FIELDS =
  'id, name, domain, website, description, country, hq_city, address, zip_code, phone, funding_stage, status, category, interesting';

export async function GET(request, { params }) {
  const { id } = await params;

  const { data, error } = await supabaseServer
    .from('companies')
    .select(SELECT_FIELDS)
    .eq('id', id)
    .maybeSingle();

  if (error) {
    return NextResponse.json({ error: error.message, hint: error.hint || null }, { status: 500 });
  }

  if (!data) {
    return NextResponse.json({ error: 'Company not found.' }, { status: 404 });
  }

  return NextResponse.json({ company: data });
}
