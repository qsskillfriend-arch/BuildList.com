# Stage 3 — Database, accounts and admin

**A product of Sharplink Ventures (U) Limited**

---

## Read this before you run anything

**You probably should not do this yet.**

Stage 3 is worth building when hand-editing JSON genuinely hurts — roughly
**200 listings**, or when firms start asking to edit their own profiles. Below
that, the admin dashboard shipped in this repo (`admin.html`) does the same job
with no server, no monthly bill, no auth to secure and no database to keep
alive.

Every week spent on a login system is a week nobody is in Kisenyi collecting
listings, and the listings are the business. If you are reading this with twelve
firms in `firms.json`, close it and go collecting.

Come back when the JSON is the bottleneck. Everything here will still work.

---

## What ships now, and what it does

| File | What it is |
|---|---|
| `admin.html` | Full content workbench. Works today, no backend. |
| `supabase/schema.sql` | Complete database: tables, indexes, row-level security, triggers. |
| `supabase/seed.sql` | Reference data — categories, districts, tiers, ad slots. |
| This file | When to migrate, how, and what will bite you. |

---

## Part 1 — The admin dashboard (available now)

### Running it

The dashboard reads `data/*.json`, so it must be served over http:

```bash
cd buildlist
python3 -m http.server 8000
# open http://localhost:8000/admin.html
```

Default passphrase: `buildlist`. Change it at the top of the `ADMIN` object
inside `admin.html`.

### Do not deploy admin.html

**The passphrase is not security.** Anyone who opens the file can read it in the
page source. It stops an idle click, nothing more.

Keep it off the live site. Add this to `.gitignore` if you deploy from the repo
root, or delete `admin.html` from the deploy folder:

```
admin.html
```

Real access control arrives with Supabase auth in Part 2. Until then, run the
workbench on your own machine.

### How publishing works

There is no server, so nothing saves itself. The flow is:

1. Edit in the dashboard. Changes are held in your browser and survive a refresh.
2. Go to **Publish**. It lists which files changed.
3. **Download** them, or **Copy** and paste over the file on GitHub.
4. Commit. Netlify redeploys in about 30 seconds.
5. Press **Mark as published** to clear the changed list.

The browser will warn you if you try to close the tab with unpublished changes.

### What the dashboard does

**Board.** Not a wall of metrics — a worklist. Problems to fix, firms awaiting
approval, tenders closing within three days, how many days since prices were
updated, listings due re-verification, unsold ad slots. Each row takes you
straight to the work. This is what the content officer opens at 08:30.

**Firms.** Search and filter, add, edit, approve, delete. Every field including
logo path, photo gallery, services, tier, status and verification date. One-click
**Approve** on a pending listing sets it live and stamps today's verification
date.

**Tenders and jobs.** Full editing, with a live "days left" pill. Anything past
its date is already hidden from the public site — you never need to delete a
stale notice, only add new ones.

**Prices.** Edited in place as a grid, because that is how the data is
collected. Warns when the index is more than ten days old.

**Advertising.** All thirteen slots listed whether sold or not, each showing
running, scheduled, paused, expired or available. "Sell" on an empty slot opens
the editor pre-filled.

**Checks.** The part that earns its keep. Catches:

- Duplicate slugs — two firms fighting over the same URL
- Category, district, tier or accreditation values not in the taxonomy, which
  make a firm silently vanish from a filter
- Listings with no phone number
- Verified badges with no date, and verifications over twelve months old
- Placeholder emails and phone numbers left in from the sample data
- Prices past their staleness threshold
- Ads pointing at slots that do not exist, ads with no link, expired campaigns
  still marked active
- Vacancies linking to firms that are not in the directory

Errors break something visible. Warnings are loose ends. Clear both before
publishing.

---

## Part 2 — Migrating to Supabase

### Why Supabase and not Node + MongoDB

The original README recommended Node, Express, MongoDB and hand-rolled JWT auth.
For a small team that means writing and then *securing* authentication, file
uploads, access control and a server. Four solved problems, four chances to get
it wrong.

Supabase gives you Postgres, authentication, file storage, row-level security
and a generated REST API with no server to run.

### The trap nobody mentions

**Free-tier projects pause after seven days without API activity.** The project
goes offline and stays offline until someone opens the dashboard and manually
restores it.

Fine while you are building. Unacceptable once firms are paying to be listed.
Either keep a scheduled job pinging the project, or move to the paid tier before
you have live users. Do not discover this over a quiet Christmas week.

Check current pricing at `supabase.com/pricing` before committing — the tiers
move.

### Setting it up

1. Create a project at supabase.com. Choose the region closest to Uganda.
2. **SQL Editor → New query** → paste `schema.sql` → Run.
3. New query → paste `seed.sql` → Run.
4. **Authentication → Users → Add user**. Create your own account.
5. Copy that user's UUID and run:

```sql
insert into staff (user_id, role, name)
values ('paste-the-uuid', 'admin', 'Your Name');
```

6. **Settings → API**. Copy the Project URL and the `anon` public key.
7. In both `index.html` and `admin.html`, set:

```javascript
ADMIN.mode = 'supabase';
ADMIN.supabase = { url: 'https://xxxx.supabase.co', anonKey: 'eyJ...' };
```

The `anon` key is safe in client code — that is what row-level security is for.
**Never put the `service_role` key in anything a browser can load.** It bypasses
every policy in the schema.

### The architecture decision that matters

**The public site does not query Supabase on every visit.** It stays static HTML.

```
Supabase  →  supabase/pull.js  →  data/*.json  →  build.js  →  703 static pages
 (edit)        (on deploy)         (committed)      (on deploy)      (served)
```

Your team edits in the database; Netlify turns it into a fast static site on every
deploy. This keeps four things you would otherwise lose:

- Pages load instantly on a 3G phone in Mukono — no database round-trip
- The 703 pages stay indexable by Google, so Stage 5 survives
- Hosting stays free
- **If Supabase pauses, breaks or hits a quota, the site is unaffected.** `pull.js`
  exits quietly and the last committed JSON is used. A slightly stale site beats
  no site.

### Step-by-step

**1. Create the project.** supabase.com → New project. Pick the region closest to
Uganda. Save the database password somewhere safe.

**2. Run the schema.** SQL Editor → New query → paste `schema.sql` → Run.
Then a new query → paste `seed.sql` → Run.

**3. Create your account.** Authentication → Users → Add user → email and password.
Copy the user's UUID, then in the SQL editor:

```sql
insert into staff (user_id, role, name)
values ('paste-the-uuid', 'admin', 'Your Name');
```

Signing in is not the same as being staff. Both the dashboard and the RLS policies
check this table.

**4. Get your keys.** Project settings → API. You need the Project URL, the `anon`
key and the `service_role` key.

```bash
cp supabase/.env.example supabase/.env
# paste all three into supabase/.env — it is gitignored
```

**5. Migrate your data.** From the site folder:

```bash
node supabase/migrate.js
```

No `npm install`. It uses plain fetch and needs nothing but Node 18+.

Expect roughly: 618 firms, their category and service links, 7 tenders, 6 jobs,
4 articles, 3 ads and 14 weeks of price history. Every insert is an upsert keyed
on slug, so **running it twice is safe** — useful if it fails halfway.

**6. Test the pull.**

```bash
node supabase/pull.js && node build.js
```

You should see the firm count come back from the database and 703 pages rebuild.

**7. Point Netlify at the database.** Site configuration → Environment variables:

| Key | Value |
|---|---|
| `SUPABASE_URL` | your project URL |
| `SUPABASE_ANON_KEY` | the anon key |
| `SITE_URL` | `https://buildlist.com` |

**Never add `SUPABASE_SERVICE_ROLE_KEY` to Netlify.** It bypasses every policy in
the schema and Netlify's build logs are not the place for it. `migrate.js` runs on
your machine only.

The build command in `netlify.toml` already reads:

```
node supabase/pull.js && node build.js
```

**8. Switch the admin over.** In `admin.html`:

```javascript
mode: 'supabase',
supabase: { url: 'https://xxxx.supabase.co', anonKey: 'eyJ...' },
```

Reload it. You now get an email and password login instead of a passphrase, and
the Publish tab saves straight to the database.

**9. Optional: one-click rebuild.** Netlify → Site configuration → Build hooks →
Add build hook. Paste the URL into `ADMIN.rebuildHook` in `admin.html` and a
"Rebuild the public site" button appears on the Publish tab.

### After migrating

Keep `data/*.json` committed. It is a free backup, it is the fallback when Supabase
is unreachable, and it is what lets you roll back a bad edit.

### What changes day to day

| | Before | After |
|---|---|---|
| Sign in | Passphrase in the source | Real account, permissions in the database |
| Saving | Download JSON, upload to GitHub, commit | One button, saves live |
| Multiple editors | Conflicts | Works properly |
| Firms editing their own listing | Not possible | Possible — build the front end when you need it |
| Public site | Static, fast | Static, fast — unchanged |

---

## The security model, in plain terms

This is the part to get right. If it is wrong, anyone can promote themselves to
Platinum from the browser console and your revenue model is decorative.

**A firm may edit its own profile. It may not touch anything commercial.**

Enforced twice, on purpose:

1. A row-level security policy limits updates to rows where `owner_id` matches
   the logged-in user.
2. A `before update` trigger overwrites `tier`, `status`, `verified`,
   `verified_at`, `tier_expires_at`, `is_group_company` and `owner_id` with
   their previous values unless the user is staff.

Belt and braces. If someone later loosens a policy by mistake, the trigger still
holds.

Other rules worth knowing:

- The public reads only `status = 'live'` firms. Pending and rejected listings
  are invisible.
- Reviews can be submitted by anyone but insert as `pending`. Only staff can
  publish. Given Ugandan defamation exposure, never let an unmoderated
  accusation about a named business reach the page.
- Ads are readable only inside their date window, so an expired campaign cannot
  keep running.
- `listing_events` accepts writes from anyone (that is how view tracking works)
  but is readable only by staff and the firm that owns the listing.

---

## What Stage 3 unlocks

- Firms edit their own descriptions, hours and photographs — removing your
  largest support burden
- Firms see their own view and contact statistics, so the renewal argument
  becomes self-service
- Firms reply to reviews, which is what makes a review system fair enough to
  defend
- Real image uploads instead of committing files to the repository
- You stop being the bottleneck

## What it still does not do

Stage 3 does not fix search visibility. Hash routes are still one page to Google.
Per-firm indexed URLs need the **Stage 5** static-site rebuild, and that remains
the single highest-value change left in the whole project.

Build Stage 3 when admin work is the bottleneck. Build Stage 5 when growth is.

---

## One design note on the price table

`price_snapshots` and `price_items` keep a dated snapshot each week rather than
overwriting one row. That is deliberate. After twelve months you own something
nobody else in Uganda has: a continuous time series of Kampala material prices.

That series is a product — sellable to contractors, banks, insurers and NGOs —
and a press-relations engine, because journalists will quote it and every quote
is a backlink. Overwriting the table would throw that away for no saving at all.
