# BuildList — Vercel launch checklist

## 1. Import the repository
Import the GitHub repository containing this project into Vercel.

The included `vercel.json` already sets:
- build command: `node supabase/pull.js && node build.js`
- static output: project root
- Vercel functions: `/api/form` and `/api/publish`
- security headers and portal no-index/no-store headers

## 2. Add these Vercel Environment Variables
Set them for **Production** (and Preview if you want to test there).

### Supabase
- `SUPABASE_URL` — your project URL
- `SUPABASE_ANON_KEY` — anon/publishable key; safe for the browser
- `SUPABASE_SERVICE_KEY` — service-role key; server-side only

### Public site
- `SITE_URL` — e.g. `https://buildlist.com`

### Forms / notifications (use at least one delivery method)
- `RESEND_API_KEY`
- `FORM_NOTIFY_EMAIL`
- `FORM_FROM_EMAIL` (optional)
- `FORM_WEBHOOK_URL` (optional alternative)

### Protected publishing
- `BUILD_HOOK_URL` — your Vercel Deploy Hook URL

**Never put `SUPABASE_SERVICE_KEY` or any other secret in browser code.**
The build creates `portal-config.js` from only `SUPABASE_URL` and `SUPABASE_ANON_KEY`.

## 3. Supabase setup
On your own computer, create `supabase/.env` from `supabase/.env.example` and run the migration using the service-role key locally. Do not upload that `.env` file to GitHub.

The public portal uses the anon/publishable key and Supabase RLS. The publish endpoint uses the server-only service key to verify staff before firing the Vercel deploy hook.

## 4. Verify after deployment
Check these before launch:

1. `/` — homepage loads and data renders.
2. `/browse/` — directory loads.
3. Open a featured firm — it should open `/firms/<slug>/`.
4. Open a tender — it should open `/tenders/<slug>/`.
5. Open a recent/sponsored article — it should open `/news/<slug>/`.
6. Open a job — it should open `/jobs/<slug>/`.
7. `/portal.html` — staff login/demo shell opens.
8. Advertise — exactly six packages are visible on desktop and each package has one CTA.
9. Header `Post Tender / Job` — opens the tender notice submission section.
10. Submit a test contact/listing/tender/advertising form and confirm it reaches the configured delivery destination.

## 5. Important launch note
The public website is usable with the committed JSON data even if Supabase is temporarily unavailable. The portal becomes fully live once the Supabase environment variables are set and the staff users/RLS are configured.
