# Staff access: two options

**BuildList.com — a product of Sharplink Ventures (U) Limited**

You now have three ways for people to edit content. Read this before setting any
of them up, because **running two at once creates two sources of truth** and you
will eventually lose somebody's work.

| | Where content lives | Login | Roles | Cost | Best for |
|---|---|---|---|---|---|
| **`admin.html`** | JSON files | Passphrase (local only) | No | Free | You, alone, right now |
| **Option A — Sveltia CMS** | JSON files in GitHub | GitHub account | Rough | Free | Two or three people editing content |
| **Option B — Supabase portal** | Postgres database | Email + password | **Yes, real** | Free → $25/mo | A team with different jobs |

## Choosing

**You asked for role dashboards, so Option B is the answer.** Sveltia can hide
collections per user but it cannot express "a content officer may add a firm but
may not set its tier". That distinction is the whole point of roles, and only a
database can enforce it.

**Pick one and commit.** If you run Sveltia and the portal together, one edits
files and the other edits a database, and whichever ran `build.js` last wins.
`supabase/pull.js` exists to pull the database back down into JSON before each
build, which resolves it — but only if the database is the single source of truth
and nobody edits the JSON directly.

My recommendation: **stay on `admin.html` until your content officer starts**,
then go straight to Option B.

---

# Option A — Sveltia CMS (free, git-based)

Your team edits at `buildlist.com/cms`. The CMS commits to GitHub and Vercel
rebuilds. No database, no monthly bill.

### 1. Point the config at your repository

In `cms/config.yml`, change:

```yaml
backend:
  name: github
  repo: YOUR-USERNAME/buildlist        # ← your actual repo
  branch: main
```

### 2. Deploy the OAuth worker

GitHub needs to authorise editors, and that handshake needs a small server. The
free way is a Cloudflare Worker.

1. **github.com → Settings → Developer settings → OAuth Apps → New OAuth App**
   - Homepage URL: `https://buildlist.com`
   - Authorization callback URL: fill in after step 2, then come back
   - Copy the **Client ID** and generate a **Client Secret**

2. Deploy the `sveltia-cms-auth` Cloudflare Worker (its README has a one-click
   deploy). Set these worker variables:
   - `GITHUB_CLIENT_ID`
   - `GITHUB_CLIENT_SECRET`
   - `ALLOWED_DOMAINS` = `buildlist.com`

3. Copy the worker URL back into the GitHub OAuth app's callback field, and into
   `cms/config.yml`:

```yaml
  base_url: https://sveltia-cms-auth.YOUR-SUBDOMAIN.workers.dev
```

### 3. Give each editor access

Add them as a **collaborator** on the GitHub repository. Anyone with write access
to the repo can edit the site. That is the model's limit — it is repo-level
permission, not per-collection roles.

### Why the GitHub backend and not Git Gateway

The classic Vercel CMS setup used Vercel Identity plus Git Gateway. Vercel's
own documentation now states that Git Gateway is deprecated, that new
configurations are not recommended, and that they will no longer fix
functionality bugs in it.

Vercel Identity itself is fine — it was scheduled for deprecation but Vercel
reversed that in February 2026. It is Git Gateway specifically that you should
avoid, which is why this config talks to GitHub directly.

---

# Option B — Supabase portal (real roles)

Staff sign in at `buildlist.com/portal` with an email and password. What they see
and what they may change depends on their role.

## Saving and publishing are not the same thing

This is the one thing to understand about the portal.

**Saving** writes to Supabase immediately. Your work is safe the moment the
toast appears; nothing can lose it.

**Publishing** rebuilds the public site. Until that runs, a visitor still sees
the previous version — because the 702 pages are generated at build time, not
fetched live. That is deliberate: it is why the site stays up when the database
is asleep, and why it loads fast on a Ugandan connection.

The top bar tracks the gap. It reads **"Site is up to date"** or
**"4 changes not on the site yet"**, and the Publish section lists exactly what
is waiting.

### Setting up the button

Create a build hook in your host and add its URL as an environment variable
named `BUILD_HOOK_URL`:

- **Netlify** — Site configuration → Build & deploy → Build hooks → Add build hook
- **Vercel** — Settings → Git → Deploy Hooks → Create Hook

**Mark it secret.** A build hook URL is a bearer token: anyone holding it can
trigger builds until the month's minutes are gone. That is exactly why the
portal never holds it. The browser asks `/api/publish`, the function checks the
caller holds a valid Supabase session belonging to a row in `staff`, and only
then fires the hook.

Without the variable the button still works and tells you plainly that nothing
is configured — rather than appearing to succeed.

### If you would rather not use it

You do not have to. Every change appears at the next deploy however that deploy
is started, including a normal commit. The button only saves you from waiting
for one.

## Two-factor authentication

TOTP, via Supabase. Works with Google Authenticator, Microsoft Authenticator or
Authy. The portal shows a QR code and a typed key for phones that cannot scan.

**Administrators must enrol.** They can set tiers, approve listings and read
every submission; a password alone is not enough for that, particularly one that
might be reused elsewhere. Editors and agents are offered it but not forced.

The check runs **before any data loads**. Fetching 618 listings and then hiding
them would mean the records had already crossed the network to a session that had
not finished proving itself.

A prompt in the interface is a courtesy, not a control. `PATCH-01.sql` includes
an `is_aal2()` function and commented-out policies so you can require a second
factor at the database level for advertising and staff. **Run those only after
you have enrolled**, or you will lock yourself out of your own controls.

Lost a device? An administrator removes the factor in Supabase under
Authentication → Users → the account → Factors, and the person enrols again.

## Listing claims

A firm presses "This is my business" on their listing. Nothing changes until
somebody **telephones the number already on the listing** and confirms it.

That call is the whole protection. Without it, claiming a competitor's listing
would be a form you fill in. It is why the review screen shows you the listed
number rather than the claimant's — a claimant confirmed on their own number has
proved nothing, because anyone can answer their own phone.

Claims appear on the Board as urgent. A decision cannot be saved without a note
saying what happened on the call, because whoever picks it up next has only that
to go on.

**Approving hands over a limited set of fields.** The owner can then correct
contact details, description, photos, services and hours. They cannot change:

| Field | Why it stays with you |
|---|---|
| Business name | |
| Web address (slug) | Changing it breaks every link the firm has shared |
| District | Moves them into a search they do not belong in |
| Tier, verification, approval | Commercial. Somebody paid, or somebody checked. |

Enforced by two database triggers, not by hiding form fields — a hidden input
stops an honest mistake, a trigger stops everything else.

Claims are visible to administrators and content officers. **Field agents do not
see them**: they collect listings, they do not adjudicate who owns one, and the
records hold a named person's phone number.

## What you can edit in the portal

| Section | What you can do |
|---|---|
| **Firms** | Add, edit, approve, set tier and verification (admin only) |
| **Tenders** | Add and edit notices. Closed ones hide themselves on the site. |
| **Jobs** | Add and edit vacancies. A closing date is required. |
| **Articles** | Write, illustrate, publish, take down |
| **Media library** | Upload images and video, attach video to a firm |
| **Prices** | Edit the weekly grid and save a dated snapshot |
| **Monthly slots** | Product of the Month (paid) and Benchmark Project (editorial) |
| **Advertising** | Campaigns and slots (admin only) |
| **Claims** | Review and decide who controls a listing (not field agents) |
| **Staff** | Who has access (admin only) |

Every section is built. Nothing says "coming next".

## Analytics: two different things

**Site-wide traffic stays in Google Analytics.** There is no point rebuilding
it, so the portal links straight into your own property: live view, pages and
traffic sources, and Search Console.

One thing to understand about those figures: the GA tag only loads for visitors
who accept the cookie notice. Your real traffic is higher than GA reports, by
whatever share declines. That is expected and lawful, not a fault.

**Per-listing activity is yours**, in the `listing_events` table, and it is the
number the whole sales argument rests on:

> "Your listing was viewed 46 times last month and 11 people tapped your number."

A field agent can put that in front of a shop owner. You could not print it from
someone else's dashboard, which is why it is recorded in your own database.

The per-listing table sorts by views and shows tier, views, contact taps and tap
rate. **A free-tier firm with 40 views and 9 taps is the easiest upgrade you
will ever sell** — you are not predicting a result, you are reporting one. Sort
by taps and work down the list.

Two rules the editors enforce, because the site depends on them:

- **A tender needs a closing date.** Without one it never expires and the board
  fills with notices that closed months ago.
- **A vacancy needs a closing date**, for the same reason. A jobs board full of
  filled positions stops being used.

Saving prices writes a **new dated snapshot** rather than overwriting the last
one. After twelve months that series is a continuous record of Kampala material
prices that nobody else holds — and it is sellable. Overwriting would throw it
away for no saving at all.

## Content studio: images and articles

Two sections in the portal, for the person who writes and illustrates.

### Media library

Drag images in. **Everything happens in the browser before upload:**

| Step | What happens |
|---|---|
| Decode | EXIF orientation applied, so a phone photo taken sideways is not stored sideways |
| Assess | Measured against the slot it is for. Too small, wrong shape or wastefully large is said plainly |
| Resize | Three widths — 1600, 800 and 400px — never upscaled |
| Encode | WebP where the browser supports it, JPEG otherwise, quality 0.82 |

A 2400×1350 photograph typically arrives **about 80% smaller** as three files.
The site then serves whichever width suits the reader through `srcset`, so a
phone on a mobile bundle in Mbale downloads the 400px one rather than the 1600px.

This is deliberately not Supabase's image transformation service, which is a paid
feature. Doing the work client-side gives the same result on the free tier, and
shrinks the file before it crosses the network rather than after.

A source smaller than the slot needs is **flagged, not stretched.** "Only 300px
wide; this slot wants 1200px. It will look soft. Ask for a larger file."

### Video

MP4, WebM and MOV, up to **45MB**. Browsers cannot re-encode video, so unlike
images the file goes up as it arrived — but three things still happen:

| | What and why |
|---|---|
| **Size cap** | Supabase Free applies a 50MB global file limit. We stop at 45MB so a file never fails at the ceiling with an opaque error. |
| **Poster frame** | We seek to one second, draw to canvas and upload the frame alongside. A video with no poster is a black rectangle until it plays, which on a slow connection is most of the time. |
| **Resumable upload** | Supabase recommends its TUS endpoint above about 6MB. A 40MB file over Ugandan mobile data will drop at least once, and a plain upload starts again from zero. Ours resumes from the last completed chunk and retries three times per chunk. |

MOV sometimes will not decode in the browser even though Supabase stores it
happily. When that happens the upload still succeeds and the portal says
"no poster (add one by hand)" rather than failing the whole thing.

**Attaching a video to a firm** writes a `firm_videos` row. `pull.js` brings it
into the generated profile, so the video appears on that firm's public page
without anyone editing JSON. Videos are muted until played — a page that starts
talking is how people close a tab.

### Article editor

Markdown with a live preview, not a rich-text box. Contenteditable produces
unpredictable HTML that breaks the first time somebody pastes from Word;
markdown stays clean and survives two people editing the same piece.

Nobody needs to know what markdown is — there are buttons for headings, bold,
italic, lists, quotes and links, and the preview updates as you type. Word count
and read time are calculated automatically.

To place an image: **Copy** on any library image, then paste into the article.
It renders with the full `srcset` and a caption from the alt text.

### Publishing and takedown

Every article has a **Take down** button. It disappears from the site
immediately and stays in the database — one click restores it. Nothing is ever
really deleted, so a mistaken takedown costs seconds rather than a rewrite.

Sponsored articles must be marked as such. The editor makes it a required
choice rather than an optional tick.

## The three roles

| | Administrator | Content officer | Field agent |
|---|---|---|---|
| Board worklist | ✓ | ✓ | ✓ |
| Add and edit firms | ✓ | ✓ | ✓ |
| **Approve a listing** | ✓ | — | — |
| **Set a tier** | ✓ | — | — |
| **Issue a verified badge** | ✓ | ✓ | — |
| Tenders, jobs, articles, prices | ✓ | ✓ | — |
| Media library — upload, attach, delete | ✓ | ✓ | — |
| Upload video and attach it to a firm | ✓ | ✓ | — |
| Write, publish and take down articles | ✓ | ✓ | — |
| Monthly slots | ✓ | ✓ | — |
| Advertising | ✓ | — | — |
| Analytics | ✓ | ✓ | — |
| Staff list | ✓ | — | — |

A field agent's submissions always arrive as **pending**. That is the point of
the role: collect fast in Kisenyi, and let somebody senior decide what goes live.

## Setup

### 1. Create the project

supabase.com → new project, region closest to Uganda. Note the database password.

### 2. Create the tables

**SQL Editor → New query** → paste `supabase/schema.sql` → Run.
New query → paste `supabase/seed.sql` → Run.

### 3. Make yourself an administrator

**Authentication → Users → Add user.** Use your real email, set a password, tick
"Auto Confirm User".

Copy the new user's UUID, then in the SQL editor:

```sql
insert into staff (user_id, role, name)
values ('paste-the-uuid', 'admin', 'Your Name');
```

### 4. Move your 618 listings across

```bash
cp supabase/.env.example supabase/.env
# paste your project URL and SERVICE ROLE key into that file
node supabase/migrate.js
```

The service_role key bypasses every security policy. It belongs in
`supabase/.env`, which `.gitignore` already excludes. **Never paste it into
`portal.html`, a deployed file, or a commit.**

### 5. Connect the portal

**Settings → API.** Copy the Project URL and the **anon** public key into the top
of `portal.html`:

```javascript
const SUPABASE_URL = 'https://xxxx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOi...';
```

The anon key is safe in client code — that is exactly what the row-level security
policies are for.

Commit, and the portal is live at `buildlist.com/portal`.

### 6. Add your team

For each person: **Authentication → Users → Add user**, then

```sql
insert into staff (user_id, role, name)
values ('their-uuid', 'editor', 'Their Name');
```

Roles are `admin`, `editor`, `agent`.

Somebody who has an account but no staff row can sign in and will see **nothing**,
with a message saying so. That is the system working.

### 7. Publish from the database

Once the database is the source of truth, the build pulls from it:

```
node supabase/pull.js && node build.js
```

That is already the build command in `vercel.json`. `pull.js` writes the
database back into `data/*.json`, then `build.js` generates the 703 pages. Set
`SUPABASE_URL` and `SUPABASE_ANON_KEY` in Vercel's environment variables and it
happens on every deploy.

If Supabase is unreachable, `pull.js` exits quietly and the committed JSON is
used. **A database outage cannot take your public site down.**

---

## Try it before you sign up for anything

Open `portal.html` with no keys configured and it offers **"Preview as
Administrator / Content officer / Field agent"**. It reads your committed JSON,
applies the real role gating, and saves nothing.

Worth ten minutes before you create a Supabase account — particularly to check
that the content officer view gives your colleague everything they need and
nothing they shouldn't have.

---

## The security model, in one paragraph

**Hiding a menu item is a courtesy. The database is the control.**

A content officer does not see the tier field. If they called the API directly
anyway, the `guard_firm_commercial_fields` trigger in `schema.sql` silently
restores `tier`, `status`, `verified`, `verified_at`, `tier_expires_at`,
`is_group_company` and `owner_id` to their previous values for anyone who is not
staff-with-permission. Row-level security means the public reads only `live`
listings, and a firm owner can edit their own record but none of the commercial
fields.

Get this wrong and anyone can make themselves Platinum from the browser console.
It is written twice on purpose.

---

## The one trap

**Free Supabase projects pause after 7 days without API activity** and stay
offline until someone opens the dashboard and restores them.

A portal your content officer uses daily will not pause. But if you both take two
weeks off, it will — and the portal will be down until you click restore. The
public site keeps working regardless, because it serves the committed JSON.

Either keep a scheduled job pinging the project, or move to the paid tier before
staff depend on it. Check current pricing at supabase.com/pricing; the tiers move.
