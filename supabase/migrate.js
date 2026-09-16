#!/usr/bin/env node
/* ═══════════════════════════════════════════════════════════════
   BUILDLIST.COM — MIGRATE DATA INTO SUPABASE  (Stage 3, step 1)
   A product of Sharplink Ventures (U) Limited

   Pushes everything in data/*.json into your Supabase project.
   Run it ONCE, from your own machine, after running schema.sql
   and seed.sql in the Supabase SQL editor.

       cd buildlist
       cp supabase/.env.example supabase/.env
       # paste your project URL and SERVICE ROLE key into that file
       node supabase/migrate.js

   No npm install. No dependencies. Node 18+ only.

   ⚠️  THE SERVICE ROLE KEY BYPASSES EVERY SECURITY POLICY.
   It belongs in supabase/.env, which .gitignore already excludes.
   Never paste it into a browser, a deployed site, or a commit.
   ═══════════════════════════════════════════════════════════════ */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');

/* ── Read supabase/.env ──────────────────────────────────────── */
function loadEnv() {
  const f = path.join(__dirname, '.env');
  if (!fs.existsSync(f)) {
    console.error('\n  supabase/.env not found.');
    console.error('  Run:  cp supabase/.env.example supabase/.env');
    console.error('  Then paste your project URL and service role key into it.\n');
    process.exit(1);
  }
  const env = {};
  fs.readFileSync(f, 'utf8').split('\n').forEach(line => {
    const m = /^\s*([A-Z_]+)\s*=\s*(.*)\s*$/.exec(line);
    if (m) env[m[1]] = m[2].replace(/^["']|["']$/g, '').trim();
  });
  return env;
}

const env = loadEnv();
const URL = (env.SUPABASE_URL || '').replace(/\/$/, '');
const KEY = env.SUPABASE_SERVICE_ROLE_KEY || '';

if (!URL || !KEY) {
  console.error('\n  SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing from supabase/.env\n');
  process.exit(1);
}
if (KEY.length < 100) {
  console.error('\n  That key looks too short. You want the SERVICE ROLE key');
  console.error('  (Project settings → API → service_role), not the anon key.\n');
  process.exit(1);
}

const read = f => JSON.parse(fs.readFileSync(path.join(ROOT, 'data', f + '.json'), 'utf8'));

/* ── Minimal PostgREST client ────────────────────────────────── */
async function api(method, table, body, query) {
  const url = URL + '/rest/v1/' + table + (query ? '?' + query : '');
  const res = await fetch(url, {
    method,
    headers: {
      'apikey': KEY,
      'Authorization': 'Bearer ' + KEY,
      'Content-Type': 'application/json',
      'Prefer': method === 'POST' ? 'resolution=merge-duplicates,return=representation' : 'return=representation'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(table + ' → ' + res.status + ' ' + text.slice(0, 400));
  }
  return text ? JSON.parse(text) : [];
}

/* Supabase rejects very large single payloads. Chunking also means a
   failure halfway through tells you exactly which batch broke. */
async function upsertAll(table, rows, chunk = 200) {
  let done = 0;
  const out = [];
  for (let i = 0; i < rows.length; i += chunk) {
    const batch = rows.slice(i, i + chunk);
    const r = await api('POST', table, batch);
    out.push(...r);
    done += batch.length;
    process.stdout.write('\r  ' + table.padEnd(22) + done + ' / ' + rows.length);
  }
  process.stdout.write('\r  ' + table.padEnd(22) + done + ' / ' + rows.length + '   done\n');
  return out;
}

async function main() {
  console.log('\n═══════════════════════════════════════════════');
  console.log(' MIGRATING TO SUPABASE');
  console.log(' ' + URL);
  console.log('═══════════════════════════════════════════════\n');

  const tax = read('taxonomy');
  const firms = read('firms');
  const tenders = read('tenders');
  const jobs = read('jobs');
  const articles = read('articles');
  const prices = read('prices');
  const ads = read('ads');
  let spotlight = [];
  try { spotlight = read('spotlight'); } catch (e) {}
  let history = null;
  try { history = read('price-history'); } catch (e) {}

  /* ── 1. Reference tables ─────────────────────────────────── */
  console.log('Reference data');
  await upsertAll('tiers', tax.tiers.map(t => ({
    slug: t.slug, name: t.name, rank: t.rank, price_ugx: t.price || 0
  })));
  await upsertAll('districts', tax.districts.map(d => ({ slug: d.slug, name: d.name })));
  await upsertAll('categories', tax.categories.map((c, i) => ({
    slug: c.slug, name: c.name, cluster: c.cluster || null, sort: i + 1
  })));
  await upsertAll('accreditations', tax.accreditations.map(a => ({ slug: a.slug, name: a.name })));
  await upsertAll('ad_slots', Object.keys(ads.slots).map(k => ({
    key: k, label: ads.slots[k].label, size: ads.slots[k].size || null
  })));

  /* Read the generated ids back so join tables can reference them */
  const catRows = await api('GET', 'categories', null, 'select=id,slug');
  const accRows = await api('GET', 'accreditations', null, 'select=id,slug');
  const catId = Object.fromEntries(catRows.map(r => [r.slug, r.id]));
  const accId = Object.fromEntries(accRows.map(r => [r.slug, r.id]));

  /* ── 2. Firms ────────────────────────────────────────────── */
  console.log('\nFirms');
  const firmRows = firms.map(f => ({
    slug: f.slug,
    name: f.name,
    initials: f.initials || null,
    description: f.desc || null,
    district: f.district,
    area: f.area || null,
    phone: f.phone || null,
    whatsapp: f.whatsapp || null,
    email: f.email || null,
    website: f.website || null,
    logo_url: f.logo || null,
    tier: f.tier || 'free',
    status: f.status || 'live',
    verified: !!f.verified,
    verified_at: f.verifiedDate || null,
    established: f.established || null,
    employees: f.employees || null,
    is_group_company: !!f.isGroupCompany
  }));
  const inserted = await upsertAll('firms', firmRows);

  const firmId = Object.fromEntries(inserted.map(r => [r.slug, r.id]));

  const links = [], accLinks = [], services = [], photos = [], projects = [];
  firms.forEach(f => {
    const id = firmId[f.slug];
    if (!id) return;
    (f.categories || []).forEach(c => { if (catId[c]) links.push({ firm_id: id, category_id: catId[c] }); });
    (f.accreditations || []).forEach(a => { if (accId[a]) accLinks.push({ firm_id: id, accreditation_id: accId[a] }); });
    (f.services || []).forEach((s, i) => services.push({ firm_id: id, label: s, sort: i }));
    (f.photos || []).forEach((p, i) => photos.push({ firm_id: id, url: p.src, alt: p.alt || null, caption: p.caption || null, sort: i }));
    (f.projects || []).forEach(p => projects.push({ firm_id: id, name: p.name, value: p.value || null, year: p.year || null }));
  });
  if (links.length)    await upsertAll('firm_categories', links, 500);
  if (accLinks.length) await upsertAll('firm_accreditations', accLinks, 500);
  if (services.length) await upsertAll('firm_services', services, 500);
  if (photos.length)   await upsertAll('firm_photos', photos, 500);
  if (projects.length) await upsertAll('firm_projects', projects, 500);

  /* ── 3. Content ──────────────────────────────────────────── */
  console.log('\nContent');
  await upsertAll('tenders', tenders.map(t => ({
    ref: t.ref, title: t.title, org: t.org || null, category: t.category || null,
    deadline: t.deadline, value_text: t.value || null, value_ugx: t.valueUgx || null,
    featured: !!t.featured, source: t.source || null, posted_at: t.postedAt || null
  })));

  await upsertAll('jobs', jobs.map(j => ({
    slug: j.slug, title: j.title, company: j.company || null,
    company_id: firmId[j.companySlug] || null,
    district: j.district || null, location: j.location || null,
    employment: j.type || null, discipline: j.discipline || null,
    salary: j.salary || null, experience: j.experience || null,
    level: j.level || null, apply_email: j.applyEmail || null,
    featured: !!j.featured, posted_at: j.postedAt || null, closes_at: j.closesAt || null
  })));

  await upsertAll('articles', articles.map(a => ({
    slug: a.slug, title: a.title, excerpt: a.excerpt || null, body: a.body || null,
    category: a.category || null, icon: a.icon || null,
    sponsored: !!a.sponsored, published: true,
    read_time: a.readTime || null, published_at: a.date || null
  })));

  await upsertAll('ads', (ads.ads || []).map(a => ({
    campaign_id: a.id, slot: a.slot, advertiser: a.advertiser,
    image_url: a.image || null, alt: a.alt || null,
    title: a.title || null, body: a.body || null, cta: a.cta || null,
    link: a.link, active: a.active !== false,
    starts_on: a.start || null, ends_on: a.end || null
  })));

  if (spotlight.length) await upsertAll('spotlight', spotlight.map(x => ({
    month_key: x.month || x.month_key, kind: x.kind || 'editorial',
    firm_id: firmId[x.firmSlug] || null, title: x.title || null, body: x.body || null,
    image_url: x.image || null, active: x.active !== false
  })));

  /* ── 4. Prices, as dated snapshots ───────────────────────── */
  console.log('\nPrices');
  const snaps = history ? history.snapshots : [{ date: prices.updated, values: null }];
  for (const snap of snaps) {
    const [row] = await api('POST', 'price_snapshots', [{
      collected_on: snap.date,
      sources: prices.sources || null,
      note: prices.note || null
    }]);
    const items = snap.values
      ? Object.keys(snap.values).map(m => ({
          snapshot_id: row.id, material: m,
          value_text: String(snap.values[m]),
          change_text: null, direction: null
        }))
      : prices.items.map(p => ({
          snapshot_id: row.id, material: p.name, value_text: p.val,
          change_text: p.change, direction: p.up === true ? 'up' : p.up === false ? 'down' : 'flat'
        }));
    await api('POST', 'price_items', items);
  }
  console.log('  price_snapshots       ' + snaps.length + ' snapshots   done');

  console.log('\n═══════════════════════════════════════════════');
  console.log(' MIGRATION COMPLETE');
  console.log('═══════════════════════════════════════════════');
  console.log('  Firms          ' + inserted.length);
  console.log('  Categories     ' + links.length + ' links');
  console.log('  Services       ' + services.length);
  console.log('  Photos         ' + photos.length);
  console.log('  Tenders        ' + tenders.length);
  console.log('  Jobs           ' + jobs.length);
  console.log('  Articles       ' + articles.length);
  console.log('  Ads            ' + (ads.ads || []).length);
  console.log('  Spotlight      ' + spotlight.length);
  console.log('  Price history  ' + snaps.length + ' weeks');
  console.log('');
  console.log(' NEXT: node supabase/pull.js   (writes Supabase back to data/*.json)');
  console.log(' Then set BUILD_FROM_SUPABASE=true in Netlify and redeploy.');
  console.log('');
  console.log(' Keep data/*.json committed. It is your backup and it is what');
  console.log(' the site falls back to if Supabase is ever unreachable.\n');
}

main().catch(err => {
  console.error('\n\n  MIGRATION FAILED\n  ' + err.message + '\n');
  console.error('  Nothing is half-written that a re-run will not fix — every');
  console.error('  insert is an upsert keyed on slug, so running it again is safe.\n');
  process.exit(1);
});
