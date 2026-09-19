# Deploying BuildList.com

**A product of Sharplink Ventures (U) Limited**

This repository deploys to **either Netlify or Vercel without changing a file.**
Both configs ship; each host reads its own and ignores the other.

| | Netlify | Vercel |
|---|---|---|
| Config | `netlify.toml` + `_redirects` | `vercel.json` |
| Form function | `netlify/functions/form.mjs` | `api/form.js` |
| Shared logic | `lib/form-core.js` | `lib/form-core.js` |
| Public form endpoint | `/api/form` | `/api/form` |
| Build command | `node supabase/pull.js && node build.js` | same |
| Publish directory | `.` | `.` |

The form endpoint is the same path on both, so nothing in the browser knows or
cares which host it is on. On Netlify `_redirects` maps `/api/form` to the
function; on Vercel it is the file path. Both import the same core, so a
submission behaves identically either way.

**We deliberately do not use Netlify Forms.** That would mean two code paths and
two sets of behaviour to keep in step. One function, one set of delivery rules,
both hosts.

---

## 1. GitHub

Push the whole folder. These must reach the repository root:

```
index.html  build.js  vercel.json  netlify.toml  _redirects
api/  netlify/  lib/  data/  images/  supabase/  downloads/
```

## 2a. Netlify

1. **Add new site → Import an existing project → GitHub →** `buildlist`
2. Settings auto-fill from `netlify.toml`:
   - Build command `node supabase/pull.js && node build.js`
   - Publish directory `.`
   - Functions directory `netlify/functions`
3. **Deploy**

## 2b. Vercel

1. **Add New → Project →** import `buildlist`
2. Framework Preset **Other**. The rest auto-fills from `vercel.json`.
   Leave Install Command blank — there are no dependencies.
3. **Deploy**

Either way the build log should end with:

```
Supabase not configured — keeping the existing data/*.json files.
  18 category shortcuts -> vercel.json + _redirects
Built 702 pages + sitemap (705 URLs)
  618 firms · 73 category pages · 6 tenders · 4 articles
```

That first line is expected when the database is not connected. `pull.js` exits
quietly and the committed JSON is used, so **a database outage cannot take the
public site down.**

## 3. Environment variables

Same names on both hosts. None are required to deploy, but forms go nowhere
useful until at least one delivery target is set.

| Variable | Purpose |
|---|---|
| `SITE_URL` | `https://buildlist.com` — canonical URLs and the sitemap. **Set this first.** |
| `SUPABASE_URL` | Project URL |
| `SUPABASE_ANON_KEY` | Used by `pull.js` at build time. Safe to expose. |
| `SUPABASE_SERVICE_KEY` | Used by the form function only. **Bypasses every security policy — never commit it or put it in any HTML file.** |
| `RESEND_API_KEY` | Emails each submission |
| `FORM_NOTIFY_EMAIL` | Where those go. Comma-separate for several. |
| `FORM_FROM_EMAIL` | Sender, once your domain is verified with Resend |
| `FORM_WEBHOOK_URL` | Optional: Slack, Make, Zapier |
| `BUILD_HOOK_URL` | **Secret.** Lets the portal's Publish button start a build. Netlify: Build hooks. Vercel: Deploy Hooks. |

Redeploy after adding them. Neither host applies new variables to an existing build.

## 4. Test the forms before announcing anything

Open `/#/submit`, fill the listing form, submit. Then check, in order:

- **Function logs** — Netlify: Functions → form. Vercel: Logs.
- Your inbox, if Resend is set
- Supabase → Table editor → `submissions`, if the database is set

With nothing configured the function still returns success and logs the
submission, and the visitor sees a normal confirmation. That is deliberate — a
visitor should never meet a server error — but it means **you must read the log
once** to confirm delivery actually works.

## 5. Domain

Add it in the host's domain settings; both issue certificates automatically.

Using Cloudflare for DNS, on either host: point `www` and the apex at the host's
target with **DNS only (grey cloud)**, and set Cloudflare SSL to **Full
(strict)**. The host must terminate TLS itself to issue its certificate —
proxying breaks it.

---

## Access: what is and is not on the server

| | Netlify | Vercel |
|---|---|---|
| `admin.html` | 404 via `_redirects`, and in `.netlifyignore` | not deployed (`.vercelignore`) |
| `supabase/` | 404 — it ships because the build needs `pull.js` | 404, same reason |
| `lib/`, `netlify/` | 404 | 404 |
| `portal.html` | served, `noindex` | served, `noindex` |

`admin.html` is protected only by a passphrase written in its own source. That
stops an idle click, not a person. **Run it locally and keep it off the server.**
The portal is the one with a real login.

---

## Moving between hosts later

Nothing to change. `build.js` writes its generated category shortcuts into
whichever config files it finds, so both stay current on every build and neither
goes stale while the other is in use.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Only the homepage exists, no `/firms/` pages | Build command blank | Set `node supabase/pull.js && node build.js` |
| Canonical URLs point at the wrong domain | `SITE_URL` unset | Add it, redeploy |
| Form returns 404 | Function not deployed | Netlify: check the functions directory is `netlify/functions`. Vercel: check `api/form.js` is in the repo. |
| Form succeeds but nothing arrives | No delivery target | Set Supabase, Resend or webhook variables and redeploy |
| Supabase video will not play | CSP | `media-src` must allow `https://*.supabase.co` — already set in both configs |
| `Error 525` on a custom domain | Cloudflare proxying | Grey cloud, SSL Full (strict) |
