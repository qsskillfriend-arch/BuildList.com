# BuildList.com — launch checklist (Vercel)

364 automated checks pass. 235 buttons and links were mapped across ten
pages; none is dead and none falls back to an unrelated page.

## Do these before you announce anything

### 1. Run the updated `supabase/schema.sql`
It adds columns the portal now writes. Safe to run more than once.
Then run `supabase/seed-ads.sql` (30 slots, 180 placeholder campaigns).

### 2. Replace the placeholder contact details
Search the code for these and put in real ones:

| Placeholder | Where it appears |
|---|---|
| `+256 700 000 000` / `256700000000` | Add-your-firm sidebar: Call and WhatsApp buttons |
| `tenders@buildlist.com` | "Email us the notice" on the Tenders page |
| `jobs@buildlist.com` | Every job's Apply button — set each employer's own address in the portal |
| `listings@buildlist.com` | The field-agent download card |
| `x.com/buildlistug`, LinkedIn, Facebook | Footer icons — point them at your real profiles |

### 3. Environment variables in Vercel
`SITE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` (not secret),
`SUPABASE_SERVICE_KEY` (secret), `BUILD_HOOK_URL` (secret) and either
`RESEND_API_KEY` + `FORM_NOTIFY_EMAIL` or `FORM_WEBHOOK_URL`.

### 4. Submit one of every form yourself
Twelve forms. Every one is now registered with the API and accepted —
tested by posting to the real handler — but only a live submission proves
your delivery (email / webhook / database) is set up.

## What changed in this pass, and why it matters

**Six forms would have failed in production.** Claims, removal requests,
tender notices, job alerts, job posts and advertising enquiries were not in
the API's list of accepted forms, so each would have returned "Unknown form".
A test now compares the site's forms against the API list so they cannot
drift apart again.

**Every deploy was quietly erasing data.** `pull.js` rewrote the category and
tier files from the database using only a few columns, which dropped the tier
capabilities (every firm would have shown as Free — no WhatsApp, no photos)
and the homepage flags (the homepage would have shown no categories). It now
merges: the database wins where it has a value, the committed files fill in
the rest. Featured firms, monthly slots, the digest sponsor and legal pages
edited in the portal now reach the site.

**Dead and misrouted controls fixed:** Subscribe, Apply Filters, Find Jobs,
Download Media Kit, Call, WhatsApp, the footer social icons (they all went to
About), Post a Tender Notice (went to Add-your-firm), Post a Job (went to the
tender form — there was no job form, so one was built), and every Apply button
(went to a placeholder inbox).

**Advertising packages:** one action each, all six on one row.

**Tier cards** are generated from the capabilities the site enforces, so what
a card promises is exactly what switches on. Starter was missing; it is back.

**Directory:** a vertical rail of six mixed-size slots (rectangle, half-page,
square, small banner), fixed heights so rotation never moves the page.

**Portal analytics:** 7 / 30 / 90-day periods, tier filter, sortable columns,
search, click a firm to focus the chart on it, a daily chart, a contact-method
breakdown, a count of free firms worth calling, and CSV and print exports.

**Removed:** the staff-portal link from the footer.
