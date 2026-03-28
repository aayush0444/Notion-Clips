# Deployment Checklist (Railway + Vercel)

## 1) Rotate leaked secrets (do first)
- OpenRouter API key
- Notion client secret
- Supabase service key
- Any other tokens you used locally

## 2) Backend (Railway) environment variables
Set these in Railway -> Variables:
- OPENROUTER_API_KEY=
- GOOGLE_API_KEY=
- YOUTUBE_API_KEY=
- SUPADATA_API_KEY=
- NOTION_CLIENT_ID=
- NOTION_CLIENT_SECRET=
- NOTION_REDIRECT_URI=https://<BACKEND_DOMAIN>/auth/notion/callback
- SUPABASE_URL=https://<SUPABASE_PROJECT>.supabase.co
- SUPABASE_SERVICE_KEY=<SERVICE_ROLE_KEY>
- FRONTEND_URL=https://<FRONTEND_DOMAIN>
- TRANSCRIPT_PRIORITY=scraping_first

Optional (only if bypassing OAuth):
- NOTION_TOKEN=
- NOTION_PAGE_ID=
- NOTION_DATABASE_ID=

## 3) Frontend (Vercel) environment variables
Set these in Vercel -> Environment Variables:
- NEXT_PUBLIC_API_URL=https://<BACKEND_DOMAIN>
- NEXT_PUBLIC_SUPABASE_URL=https://<SUPABASE_PROJECT>.supabase.co
- NEXT_PUBLIC_SUPABASE_ANON_KEY=<ANON_KEY>

## 4) Notion OAuth settings
In Notion Integrations settings:
- Redirect URL: https://<BACKEND_DOMAIN>/auth/notion/callback
- Ensure the integration is shared with the target workspace

## 5) Supabase Auth settings
In Supabase -> Authentication -> URL Configuration:
- Site URL: https://<FRONTEND_DOMAIN>
- Add Redirect URLs:
  - https://<FRONTEND_DOMAIN>/app
  - https://<FRONTEND_DOMAIN>

## 6) Smoke tests (after deploy)
- GET https://<BACKEND_DOMAIN>/health
- Notion connect button completes OAuth and returns to /app
- Google sign-in completes and returns to /app
- Push to Notion creates a page
