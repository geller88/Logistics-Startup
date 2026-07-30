import { NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabaseServerClient';

export async function POST(request) {
  const { user_id, plan, message } = await request.json();

  if (!user_id || !plan || !message || message.trim().length === 0) {
    return NextResponse.json({ error: 'user_id, plan, and message are required.' }, { status: 400 });
  }

  const { error } = await supabaseServer.from('premium_requests').insert({
    user_id,
    plan,
    message: message.trim(),
    status: 'submitted',
  });

  if (error) {
    return NextResponse.json({ error: error.message, hint: error.hint || null }, { status: 500 });
  }

  return NextResponse.json({ success: true });
}
