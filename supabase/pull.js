#!/usr/bin/env node
/* ═══════════════════════════════════════════════════════════════
   BUILDLIST.COM — PULL FROM SUPABASE  (Stage 3, step 2)
   A product of Sharplink Ventures (U) Limited

   Reads the live database and writes data/*.json, so build.js can
   generate the 703 static pages from it exactly as before.

   This is the design decision that matters. The public site does NOT
   query Supabase on every visit. It stays static HTML, which means:

     · pages still load instantly on a 3G phone in Mukono
     · the 703 pages stay indexable by Google (Stage 5 survives)
     · hosting stays free
     · if Supabase is down, paused or over quota, the site is fine

   Supabase becomes the place your team edits, and the build turns it
   into a fast static site. You get accounts and a real admin without
   giving up the thing that makes the site work.

   Run locally:   node supabase/pull.js
   On Vercel:    handled automatically — see vercel.json

   Uses the ANON key only. It reads what the public can read.
   ═══════════════════════════════════════════════════════════════ */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const DATA = path.join(ROOT, 'data');

const URL = (process.env.SUPABASE_URL || readEnv('SUPABASE_URL') || '').replace(/\/$/, '');
const KEY = process.env.SUPABASE_ANON_KEY || readEnv('SUPABASE_ANON_KEY') || '';

function readEnv(name) {
  const f = path.join(__dirname, '.env');
  if (!fs.existsSync(f)) return '';
  const m = new RegExp('^\\s*' + name + '\\s*=\\s*(.*)$', 'm').exec(fs.readFileSync(f, 'utf8'));
  return m ? m[1].replace(/^["']|["']$/g, '').trim() : '';
}

if (!URL || !KEY) {
  console.log('  Supabase not configured — keeping the existing data/*.json files.');
  console.log('  (Set SUPABASE_URL and SUPABASE_ANON_KEY to pull from the database.)');
  process.exit(0);
}

async function get(table, query) {
  const res = await fetch(URL + '/rest/v1/' + table + '?' + query, {
    headers: { apikey: KEY, Authorization: 'Bearer ' + KEY }
  });
  if (!res.ok) throw new Error(table + ' → ' + res.status + ' ' + (await res.text()).slice(0, 300));
  return res.json();
}

/* Paged, because PostgREST caps a single response at 1,000 rows and
   you will pass that on firms sooner than you think. */
async function getAll(table, query) {
  const out = [];
  const size = 1000;
  for (let from = 0; ; from += size) {
    const res = await fetch(URL + '/rest/v1/' + table + '?' + query, {
      headers: {
        apikey: KEY, Authorization: 'Bearer ' + KEY,
        Range: from + '-' + (from + size - 1)
      }
    });
    if (!res.ok) throw new Error(table + ' → ' + res.status + ' ' + (await res.text()).slice(0, 300));
    const batch = await res.json();
    out.push(...batch);
    if (batch.length < size) break;
  }
  return out;
}

const write = (file, obj) => {
  fs.writeFileSync(path.join(DATA, file), JSON.stringify(obj, null, 2) + '\n');
  console.log('  data/' + file.padEnd(22) + (Array.isArray(obj) ? obj.length + ' records' : 'written'));
};

async function main() {
  console.log('\n  Pulling from ' + URL + '\n');

  /* ── Taxonomy ────────────────────────────────────────────── */
  const [cats, dists, accs, tiers, slots] = await Promise.all([
    get('categories', 'select=slug,name,cluster&order=sort'),
    get('districts', 'select=slug,name&order=name'),
    get('accreditations', 'select=slug,name&order=name'),
    get('tiers', 'select=slug,name,rank,price_ugx&order=rank'),
    get('ad_slots', 'select=key,label,size')
  ]);

  write('taxonomy.json', {
    categories: cats,
    districts: dists,
    accreditations: accs,
    tiers: tiers.map(t => ({ slug: t.slug, name: t.name, rank: t.rank, price: t.price_ugx }))
  });

  /* ── Firms, with their joined rows ───────────────────────── */
  const firms = await getAll('firms',
    'select=*,firm_categories(categories(slug)),firm_accreditations(accreditations(slug)),' +
    'firm_services(label,sort),firm_photos(url,alt,caption,sort),firm_projects(name,value,year),' +
    'firm_videos(url,poster_url,title,caption,mime,duration,sort)' +
    '&status=eq.live&order=name');

  const firmJson = firms.map((f, i) => ({
    id: i + 1,
    slug: f.slug,
    name: f.name,
    initials: f.initials || '',
    categories: (f.firm_categories || []).map(r => r.categories.slug),
    district: f.district,
    area: f.area || '',
    address: f.area || '',
    desc: f.description || '',
    descSource: 'database',
    services: (f.firm_services || []).sort((a, b) => a.sort - b.sort).map(s => s.label),
    rating: 0,
    reviews: 0,
    tier: f.tier,
    status: f.status,
    accreditations: (f.firm_accreditations || []).map(r => r.accreditations.slug),
    phone: f.phone || '',
    whatsapp: f.whatsapp || f.phone || '',
    email: f.email || '',
    website: f.website || '',
    logo: f.logo_url || '',
    /* Videos attached in the portal become part of the generated
       profile, so a firm's walkthrough appears on its public page
       without anyone editing JSON. */
    videos: (f.firm_videos || [])
      .sort((a, b) => (a.sort || 0) - (b.sort || 0))
      .map(v => ({ src: v.url, poster: v.poster_url || '', title: v.title || '',
                   caption: v.caption || '', mime: v.mime || 'video/mp4',
                   duration: v.duration || 0 })),
    photos: (f.firm_photos || []).sort((a, b) => a.sort - b.sort)
      .map(p => ({ src: p.url, alt: p.alt || '', caption: p.caption || '' })),
    projects: (f.firm_projects || []).map(p => ({ name: p.name, value: p.value, year: p.year })),
    established: f.established || '',
    employees: f.employees || '',
    verified: !!f.verified,
    verifiedDate: f.verified_at,
    isGroupCompany: !!f.is_group_company,
    createdAt: (f.created_at || '').slice(0, 10),
    lat: 0.3476, lng: 32.5825, geoPrecision: 'district'
  }));

  /* Ratings come from published reviews, never from a stored number */
  const reviews = await getAll('reviews', 'select=firm_id,rating&status=eq.published');
  const agg = {};
  reviews.forEach(r => {
    agg[r.firm_id] = agg[r.firm_id] || { n: 0, sum: 0 };
    agg[r.firm_id].n++; agg[r.firm_id].sum += r.rating;
  });
  firms.forEach((f, i) => {
    const a = agg[f.id];
    if (a) { firmJson[i].reviews = a.n; firmJson[i].rating = Math.round((a.sum / a.n) * 10) / 10; }
  });

  write('firms.json', firmJson);

  /* ── Tenders and jobs ────────────────────────────────────── */
  const tenders = await getAll('tenders', 'select=*&order=deadline');
  write('tenders.json', tenders.map(t => ({
    ref: t.ref, title: t.title, org: t.org, deadline: t.deadline,
    value: t.value_text, valueUgx: t.value_ugx, category: t.category,
    featured: t.featured, source: t.source, postedAt: t.posted_at
  })));

  const jobs = await getAll('jobs', 'select=*,firms(slug)&order=posted_at.desc');
  write('jobs.json', jobs.map(j => ({
    slug: j.slug, title: j.title, company: j.company,
    companySlug: j.firms ? j.firms.slug : '',
    district: j.district, location: j.location, type: j.employment,
    discipline: j.discipline, salary: j.salary, experience: j.experience,
    level: j.level, postedAt: j.posted_at, closesAt: j.closes_at,
    featured: j.featured, applyEmail: j.apply_email
  })));

  /* ── Articles ────────────────────────────────────────────── */
  const articles = await getAll('articles', 'select=*&published=is.true&order=published_at.desc');
  write('articles.json', articles.map(a => ({
    slug: a.slug, title: a.title, excerpt: a.excerpt, body: a.body,
    category: a.category, icon: a.icon, date: a.published_at,
    readTime: a.read_time, sponsored: a.sponsored, main: false
  })));

  /* ── Prices: latest snapshot plus the full series ─────────── */
  const snaps = await getAll('price_snapshots', 'select=*,price_items(*)&order=collected_on.desc');
  if (snaps.length) {
    const latest = snaps[0];
    write('prices.json', {
      updated: latest.collected_on,
      sources: latest.sources || [],
      note: latest.note || '',
      items: (latest.price_items || []).map(p => ({
        name: p.material, val: p.value_text, change: p.change_text || '0%',
        up: p.direction === 'up' ? true : p.direction === 'down' ? false : null
      }))
    });

    const materials = [...new Set(snaps.flatMap(s => (s.price_items || []).map(p => p.material)))];
    write('price-history.json', {
      _readme: 'Generated from Supabase price_snapshots. Do not edit by hand.',
      materials,
      snapshots: snaps.slice().reverse().map(s => ({
        date: s.collected_on,
        values: Object.fromEntries((s.price_items || []).map(p =>
          [p.material, parseInt(String(p.value_text).replace(/[^\d]/g, ''), 10) || 0]))
      }))
    });
  }

  /* ── Ads ─────────────────────────────────────────────────── */
  const ads = await getAll('ads', 'select=*');
  write('ads.json', {
    _readme: 'Generated from Supabase. Edit in the admin dashboard, not here.',
    slots: Object.fromEntries(slots.map(s => [s.key, { label: s.label, size: s.size }])),
    ads: ads.map(a => ({
      id: a.campaign_id, slot: a.slot, advertiser: a.advertiser,
      image: a.image_url || '', alt: a.alt || '',
      title: a.title || '', body: a.body || '', cta: a.cta || '',
      link: a.link, active: a.active, start: a.starts_on, end: a.ends_on
    }))
  });

  console.log('\n  Pull complete. build.js will now generate pages from this data.\n');
}

main().catch(err => {
  console.error('\n  PULL FAILED: ' + err.message);
  console.error('  Keeping the existing data/*.json so the build still succeeds.');
  console.error('  The site will deploy with the last known good data.\n');
  process.exit(0);   // deliberately not a failure — a stale site beats no site
});
