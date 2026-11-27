// Optional Supabase Auth. When NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY are unset the
// app runs in local single-user mode and no token is sent (the backend must have REQUIRE_AUTH=false).
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

let client: SupabaseClient | null = null;

export function supabaseEnabled(): boolean {
  return Boolean(url && key);
}

export function getSupabase(): SupabaseClient | null {
  if (!supabaseEnabled()) return null;
  if (!client) client = createClient(url!, key!);
  return client;
}

export async function getAccessToken(): Promise<string | null> {
  const sb = getSupabase();
  if (!sb || typeof window === "undefined") return null;
  const { data } = await sb.auth.getSession();
  return data.session?.access_token ?? null;
}
