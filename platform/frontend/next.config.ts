import type { NextConfig } from "next";

// The browser talks to the FastAPI backend directly at NEXT_PUBLIC_API_URL. Only public values
// (API URL, Supabase URL and publishable key) are exposed to the client; no secrets live here.
const nextConfig: NextConfig = { reactStrictMode: true };

export default nextConfig;
