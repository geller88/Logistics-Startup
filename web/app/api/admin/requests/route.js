import { NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabaseServerClient';

const adminEmails = process.env.ADMIN_EMAILS?.split(',').map((email) => email.trim().toLowerCase()) || [];

export async function GET(request) {
  const authHeader = request.headers.get('Authorization') || '';
  const token = authHeader.replace('Bearer ', '').trim();

  if (!token) {
    return NextResponse.json({ error: 'Authorization token required.' }, { status: 401 });
  }

  const { data: userData, error: userError } = await supabaseServer.auth.getUser(token);
  if (userError || !userData?.user) {
    return NextResponse.json({ error: 'Invalid auth token.' }, { status: 401 });
  }

  const email = userData.user.email?.toLowerCase();
  if (!email || !adminEmails.includes(email)) {
    return NextResponse.json({ error: 'Unauthorized.' }, { status: 403 });
  }

  const { data, error } = await supabaseServer
    .from('premium_requests')
    .select('id, user_id, plan, message, status, created_at')
    .order('created_at', { ascending: false })
    .limit(100);

  if (error) {
    return NextResponse.json({ error: error.message, hint: error.hint || null }, { status: 500 });
  }

  return NextResponse.json({ requests: data });
}
