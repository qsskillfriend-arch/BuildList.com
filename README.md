# BuildList.com

### Uganda's Construction Industry Directory
**A product of Sharplink Ventures (U) Limited**

> A monetised construction industry directory for Uganda — QS firms, architects, engineers, contractors, material suppliers, live tenders, jobs and material prices. One static HTML file, no build step, deployable in about ten minutes.

---

## Read this first

**Stage 1 of the build guide is implemented.** The site is no longer a
prototype with decorative controls — search searches, filters filter, counts
are computed, and every firm has its own page. What follows is what changed and
what you still need to do.

### Content now lives in `/data`, not in `index.html`

All firms, tenders, jobs, articles and prices are JSON files in `data/`. Read
`data/README.md` before editing them — it covers the schema and the rules that
matter (slugs are permanent, category values must match the taxonomy).

**`data/firms.json` ships with 12 sample records. Delete or replace all of them
before you publish.** Some use names resembling real Ugandan firms, and
publishing a real business's contact details without consent conflicts with the
Data Protection and Privacy Act, 2019 and with the consent commitment on your
own About page.

### Headline numbers are config-driven and start honest

The `SITE` object at the top of the `<script>` block drives every figure on the
site. It ships with `preLaunch: true`, which counts the firms actually in your
data and labels media-kit audience figures as targets rather than measured
results. Set it to `false` only when Google Analytics can evidence the numbers —
any advertiser paying seven figures a month will ask to see them.

### Regulator partnership claims were removed

The About page previously claimed "Official data partnerships with ARB,
UIPE, and PPDA". Unless you hold signed agreements, that is a real exposure. It
now says you check listings against those bodies' **public registers**, with an
explicit disclosure that you are not affiliated with or endorsed by them.

### The site must be served over HTTP

Because it now fetches `data/*.json`, opening `index.html` directly from a
folder will show a load error explaining exactly that. Run a local server:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

Vercel, GitHub Pages and every other host serve it correctly.

---

## What now works

| Feature | Behaviour |
|---|---|
| Hero + directory search | Matches firm name, description, area, services and category |
| Sidebar filters | Category, district, tier, accreditation, minimum rating — all live |
| Facet counts | Computed from the data. A category showing 0 is information, not a bug |
| Active filter chips | Show what is applied, each individually removable |
| Sort | Relevance, rating, name, most reviewed, recently added |
| Default ranking | Paid tiers first — the business model, disclosed on the page |
| Per-firm pages | `#/firms/palm-associates-uganda`, shareable, with its own `<title>` |
| Shareable filtered views | `#/directory?cat=architecture-firms&dist=kampala` |
| Tenders | Closed notices hide automatically; within 14 days flags "Closing Soon" |
| Jobs | Expire automatically; filter by discipline, district and level |
| Contact tracking | Every WhatsApp, call and email tap fires an analytics event |
| Firm logos | Image if supplied, coloured initials if not — never a broken image |
| Firm photo galleries | Up to any number, shown on the profile page |
| Ad slots | 13 slots driven from `data/ads.json`, with automatic start/end dates |
| Unsold ad inventory | Shows "slot available" with your sales email |
| List / Grid / Map views | All three work; the view is carried in the URL |
| Map | Leaflet + OpenStreetMap, no API key, with an offline fallback list |
| Static pages (Stage 5) | `node build.js` generates a real indexable page per firm, category, category×district, tender and article |
| Price index (Stage 6) | 14 weeks of sparklines plus CSV download |
| Tender alerts (Stage 6) | Category and value-band signup |
| Request for quote (Stage 6) | Matches up to 5 verified suppliers live as you choose |
| Empty states | Offer to add the missing firm — turning a dead end into a lead |
| Loading + error states | Skeletons while loading; a plain explanation if data fails |

### The analytics event that matters

Every contact tap fires `listing_contact` with the firm slug, method and tier.
This is the foundation of the Phase 3 sales conversation — *"your listing was
viewed 46 times last month and 11 people tapped your number"* — which is the
only argument that reliably converts a free listing to a paid one. Install GA4
before you start collecting listings, not after.

---

## Managing content

Open `admin.html` **locally** — never deploy it, the passphrase is in the source:

```bash
python3 -m http.server 8000
# http://localhost:8000/admin.html   passphrase: buildlist
```

Edit firms, tenders, jobs, articles, prices and advertising in a proper
interface, run the integrity checks, then download the changed JSON files and
commit them. Full detail in `supabase/README.md`.

---

## Building the static pages

```bash
node build.js        # no dependencies, Node 18+
```

Generates a real HTML file per firm, category, category-and-district, tender and
article, each with its own title, description, canonical URL and structured
data — plus the sitemap. Vercel runs it on every deploy, so committing a JSON
change rebuilds every affected page.

Generated folders (`/firms`, `/browse`, `/tenders`, `/news`) are gitignored.
They are output, not source.

Set `SITE_URL` in Vercel's environment variables once your real domain is live,
so canonical URLs and the sitemap match.

## What still does not work

- User accounts, firm login, self-service editing — Stage 3, see `supabase/`
- Review submission (ratings shown are carried from verification calls)
- **Payment collection — Stage 4, deliberately skipped.** Invoice your first
  customers by hand over mobile money. It is slower per customer, far faster to
  launch, and teaches you what advertisers negotiate.

---

## What's inside

| Page | Route | Description |
|---|---|---|
| Homepage | `/` | Hero search, live price ticker, featured listings, tenders, jobs, news, newsletter |
| Directory | `/directory` | Firm listings with sidebar filters, tier badges, ratings, in-feed ads |
| Company Profile | `/#/profile` | Full firm detail — stats, services, projects, reviews, contact sidebar |
| Tenders Board | `/tenders` | Procurement notices with reference numbers, values, deadline urgency |
| Jobs Board | `/jobs` | Construction vacancies with salary guide sidebar |
| News & Prices | `/news` | Articles, sponsored content, material price index |
| Advertise | `/advertise` | Media kit, audience profile, six ad packages with UGX pricing |
| Submit Listing | `/submit` | Four-tier membership selector plus full firm application form |
| About | `/about` | Mission, ownership and governance, verification method, team, contact |

---

## File structure

```
buildlist/
├── index.html          ← Site shell: 9 pages, CSS, JS, icon sprite
├── admin.html          ← ADMIN WORKBENCH — run locally, do NOT deploy
├── 404.html            ← Not-found page
├── supabase/           ← Stage 3 database (optional, see supabase/README.md)
│   ├── README.md       ← When to migrate and how
│   ├── schema.sql      ← Tables, indexes, row-level security
│   └── seed.sql        ← Reference data
├── build.js            ← STAGE 5 generator — real HTML page per firm/category
├── data/               ← ALL CONTENT LIVES HERE — see data/README.md
│   ├── taxonomy.json   ← Categories, districts, accreditations, tiers
│   ├── firms.json      ← Firm listings (12 samples — replace them)
│   ├── tenders.json    ← Procurement notices (auto-expire)
│   ├── jobs.json       ← Vacancies (auto-expire)
│   ├── articles.json   ← News and guides
│   ├── prices.json     ← Material price index + collection date
│   ├── ads.json        ← Advertisement inventory (13 slots)
│   └── price-history.json ← Weekly price snapshots — the time series
├── images/             ← Logos, firm photos, ad creatives
│   ├── README.md       ← HOW TO ADD IMAGES — sizes, workflow, rules
│   ├── logos/          ← Firm logos (400x400 PNG)
│   ├── firms/          ← Firm photographs (1200x900 JPG)
│   └── ads/            ← Advertiser banner creatives
├── og-image.png        ← 1200x630 social share preview (WhatsApp, Facebook, LinkedIn)
├── icon-192.png        ← PWA icon
├── icon-512.png        ← PWA icon (also used as maskable)
├── favicon.svg         ← Brand favicon, scales to any size
├── manifest.json       ← PWA install configuration
├── vercel.json        ← Deploy config, security headers, cache policy
├── _redirects          ← Clean URLs (/directory → /#/directory) and catch-all
├── robots.txt          ← Crawl rules, including AI-crawler blocks
├── sitemap.xml         ← Pages for Google and Bing
├── .gitignore
└── README.md           ← This file
```

---

## Deploy to Vercel

### Step 1 — Create a GitHub repository

1. github.com → **New repository**
2. Name it `buildlist`
3. **Public** (required for free Vercel builds) or Private (needs Vercel Pro)
4. Do **not** initialise with a README — you already have one
5. **Create repository**

### Step 2 — Upload the files

**Web interface (no Git needed):** open the repo → **uploading an existing file** → drag every file from this folder in → commit.

**Command line:**
```bash
cd buildlist
git init
git add .
git commit -m "Initial commit — BuildList.com"
git remote add origin https://github.com/YOUR-USERNAME/buildlist.git
git branch -M main
git push -u origin main
```

### Step 3 — Deploy

1. vercel.com → sign up with GitHub
2. **Add new site** → **Import an existing project** → **GitHub**
3. Pick the repo. Build settings auto-detect from `vercel.json`: build command empty, publish directory `.`
4. **Deploy site** → live in about 30 seconds

### Step 4 — Custom domain

1. Vercel → **Domain settings** → **Add custom domain**
2. Enter your domain, then update nameservers at your registrar
3. Allow up to 48 hours for DNS; SSL is issued and renewed automatically

Registrars: **registry.co.ug** for `.co.ug` (around UGX 80,000/year) · **Namecheap** for `.com` (around USD 10/year).

### Step 5 — Forms

Three forms are already wired with `data-vercel="true"` and honeypot spam protection: `newsletter`, `contact` and `listing-submission`. They work as soon as you deploy — no extra setup.

Submissions appear in **Vercel Dashboard → Forms**. Turn on email alerts under **Forms → [form name] → Settings → Notifications**. Free tier covers 100 submissions a month.

When you open `index.html` as a local file the forms can't post anywhere, so they show a preview confirmation instead. That's expected.

---

## Updating the site

```bash
# 1. Edit index.html
# 2. Commit
git add .
git commit -m "Add 10 new firms to directory"
# 3. Push — Vercel redeploys in ~30 seconds
git push
```

---

## Customisation

### The config object — start here

Near the top of the `<script>` block in `index.html`:

```javascript
const SITE = {
  name:      'BuildList.com',
  owner:     'Sharplink Ventures (U) Limited',
  domain:    'buildlist.com',
  email:     'hello@buildlist.com',
  adsEmail:  'advertising@buildlist.com',
  phone:     '+256 700 000 000',
  address:   'Plot 18, Kampala Road, Kampala',

  preLaunch: true,        // ← see "Read this first" above

  stats: {
    firms:     null,      // null = count the LISTINGS array automatically
    districts: 12,
    tenders:   null,      // null = count TENDERS
    jobs:      null,      // null = count JOBS
    visitors:  0,         // from Google Analytics
    subs:      0          // from your mailing list
  },
  targets: { visitors: 15000, subs: 1500 }
};
```

Change a value here and it updates everywhere on the site. Contact details flow into the About page automatically.

### Colours

Find the `:root` block at the top of the `<style>` section:

```css
:root {
  --forest:    #1A3C2A;   /* dark green — header, hero, footer */
  --gold:      #C49A16;   /* accent, CTAs */
  --parchment: #F8F6F1;   /* warm off-white page background */
  --red:       #B83232;   /* urgent / alert */
}
```

### Firm listings

Find `const LISTINGS` in the `<script>` block:

```javascript
{
  id: 1,
  name: 'Palm Associates Uganda Ltd',
  initials: 'PA',
  category: 'Quantity Surveyors',
  desc: 'Real description here...',
  location: 'Nakasero, Kampala',
  rating: 4.8,
  reviews: 47,
  tier: 'platinum',    // 'free' | 'verified' | 'premium' | 'platinum'
  tags: ['ARB Reg.', 'ISO 9001']
}
```

`TENDERS`, `JOBS`, `NEWS` and `PRICES` follow the same pattern. Update `PRICES` weekly — a stale price index is worse than none, because people quote from it.

### Icons

Icons come from a sprite at the top of `<body>`. Use one anywhere with:

```html
<svg class="ic" aria-hidden="true"><use href="#i-search"></use></svg>
```

Available: `search` `pin` `award` `shield-check` `lock` `activity` `smartphone` `bar-chart` `clipboard` `cash` `briefcase` `newspaper` `megaphone` `globe` `building` `bell` `info` `ruler` `institution` `tool` `download` `upload` `mail` `phone` `scale` `chat` `clock` `folder` `plus` `bricks` `alert` `map` `graduation` `crane` `hospital` `bulb` `flag` `users` `settings` `chevron-down` `menu` `close` `calendar` `whatsapp` `linkedin` `facebook` `x-social` `external`.

Icons inherit `color` and scale with `font-size`. Add `class="ic ic-lg"` for a larger one. **Don't reintroduce emoji** — that is the problem this replaced.

### Advertising slots

Search for `ad-unit` and swap the placeholder for your advertiser's banner or your AdSense code:

```html
<ins class="adsbygoogle"
  style="display:block"
  data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
  data-ad-slot="XXXXXXXXXX"
  data-ad-format="auto"></ins>
```

If you add AdSense, note that `vercel.json` contains a Content Security Policy. You will need to add Google's ad domains to `script-src` and `frame-src` or the ads will be blocked.

---

## After deployment

- [ ] Replace `buildlist.com` with your real domain in `sitemap.xml`, `robots.txt`, and the `og:` and `canonical` meta tags in `index.html`
- [ ] Fill in the URSB registration number and URA TIN on the About page — they currently read `[insert]`, and advertisers and regulators both check them
- [ ] Submit the sitemap to [Google Search Console](https://search.google.com/search-console) and [Bing Webmaster Tools](https://www.bing.com/webmasters)
- [ ] Create a GA4 property and paste the tag before `</head>`
- [ ] Test a WhatsApp share — the `og-image.png` preview should render
- [ ] Register on Google Business Profile if you have a physical office
- [ ] Have a lawyer review the Terms of Service and Privacy Policy before publishing them; the footer links currently point at the About page as placeholders
- [ ] Register with the Personal Data Protection Office — you are storing personal data of listed businesses, which the Data Protection and Privacy Act, 2019 covers

---

## Roadmap

### Phase 1 — Content (Months 1–3)
- [ ] Add 100+ real firm listings from the ARB, ERB and SRB public registers
- [ ] Weekly manual tender updates from the PPDA portal
- [ ] Publish the first 10 SEO articles on Uganda construction keywords
- [ ] Connect Google Analytics
- [ ] Confirm Vercel form notifications reach a monitored inbox

### Phase 2 — Backend (Months 3–6)

The single highest-value change is giving each firm and each category a **real URL** — `/firms/palm-associates-uganda`, `/quantity-surveyors-kampala` — instead of hash routes. Google treats the whole site as one page right now. A thousand listings should be a thousand indexed pages, and that is where directory traffic actually comes from.

Suggested stack:

```
Frontend:  This HTML file, largely unchanged
Backend:   Node.js + Express
Database:  MongoDB Atlas (free tier, 512MB)
Auth:      JWT
Host:      Railway.app or Render.com (free tier)
```

Unlocks firm self-service profiles, automated tender ingestion, Flutterwave payments for listing fees, email verification, and an admin approval dashboard.

### Phase 3 — Growth (Months 6–12)
- [ ] Move to Cloudflare Pages for unlimited bandwidth and faster East Africa delivery
- [ ] Per-firm and per-category pages (see Phase 2)
- [ ] Wrap in Capacitor.js for an Android app
- [ ] Ezoic once monthly visitors pass 10,000
- [ ] Premium tender alert email service

---

## Monetisation

| Revenue stream | Where | Starting price (UGX) |
|---|---|---|
| Platinum listing | Directory featured spot | 1,500,000/year |
| Premium listing | Priority search placement | 400,000/year |
| Homepage leaderboard | Top of homepage | 2,000,000/month |
| Newsletter sponsorship | Weekly digest | 500,000/send |
| Featured tender notice | Tenders board | 500,000/notice |
| Featured job posting | Jobs board | 250,000/post |
| Sponsored article | News section | 2,000,000/article |
| Tender board sponsor | All tender pages | 600,000/month |
| Google AdSense | All pages, passive | Variable |

These are list prices. Expect to discount heavily for the first ten advertisers — early logos are worth more than early revenue, because the eleventh advertiser buys partly on seeing who came before.

---

## Hosting comparison

| | Vercel (free) | GitHub Pages | Vercel | Cloudflare Pages |
|---|---|---|---|---|
| Bandwidth | 100 GB/mo | 100 GB/mo | 100 GB/mo | **Unlimited** |
| Form handling | **Built in** | No | No | No |
| CDN | Yes | Yes | Yes | Yes (fastest in Africa) |
| Free SSL | Yes | Yes | Yes | Yes |
| Instant rollback | Yes | No | Yes | Yes |
| Beginner friendly | Highest | Medium | High | Medium |

Start on Vercel — the built-in form handling alone saves you a backend. Move to Cloudflare Pages past roughly 50,000 monthly visitors.

---

## Support

Platform enquiries: **hello@buildlist.com**
Advertising: **advertising@buildlist.com**

---

## Licence

© 2026 Sharplink Ventures (U) Limited. All rights reserved.

BuildList.com is a product of Sharplink Ventures (U) Limited, registered in Uganda. This codebase is proprietary. Do not redistribute or deploy copies without written permission.
