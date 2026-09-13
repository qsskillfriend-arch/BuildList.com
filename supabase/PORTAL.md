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

Your team edits at `buildlist.com/cms`. The CMS commits to GitHub and Netlify
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

The classic Netlify CMS setup used Netlify Identity plus Git Gateway. Netlify's
own documentation now states that Git Gateway is deprecated, that new
configurations are not recommended, and that they will no longer fix
functionality bugs in it.

Netlify Identity itself is fine — it was scheduled for deprecation but Netlify
reversed that in February 2026. It is Git Gateway specifically that you should
avoid, which is why this config talks to GitHub directly.

---

# Option B — Supabase portal (real roles)

Staff sign in at `buildlist.com/portal` with an email and password. What they see
and what they may change depends on their role.

## The three roles

| | Administrator | Content officer | Field agent |
|---|---|---|---|
| Board worklist | ✓ | ✓ | ✓ |
| Add and edit firms | ✓ | ✓ | ✓ |
| **Approve a listing** | ✓ | — | — |
| **Set a tier** | ✓ | — | — |
| **Issue a verified badge** | ✓ | ✓ | — |
| Tenders, jobs, articles, prices | ✓ | ✓ | — |
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

That is already the build command in `netlify.toml`. `pull.js` writes the
database back into `data/*.json`, then `build.js` generates the 703 pages. Set
`SUPABASE_URL` and `SUPABASE_ANON_KEY` in Netlify's environment variables and it
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
