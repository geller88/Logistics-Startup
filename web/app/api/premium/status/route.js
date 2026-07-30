import { NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabaseServerClient';

export async function PATCH(request) {
  const { id, status } = await request.json();

  if (!id || !status) {
    return NextResponse.json({ error: 'id and status are required.' }, { status: 400 });
  }

  const { error } = await supabaseServer
    .from('premium_requests')
    .update({ status })
    .eq('id', id);

  if (error) {
    return NextResponse.json({ error: error.message, hint: error.hint || null }, { status: 500 });
  }

  return NextResponse.json({ success: true });
}
