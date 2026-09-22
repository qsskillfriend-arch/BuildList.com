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

/* Read what is already committed, so the database can win where it has
   a value and the committed file fills in anything it does not.

   Without this, every build overwrote taxonomy.json with only the
   columns the database happened to have — silently erasing tier
   capabilities (so every firm rendered as Free) and the homepage
   category flags (so the homepage showed no categories at all). */
const existing = file => {
  try { return JSON.parse(fs.readFileSync(path.join(DATA, file), 'utf8')); }
  catch (e) { return null; }
};
const bySlug = (list, key = 'slug') =>
  Object.fromEntries((list || []).map(x => [x[key], x]));

/* Ask for optional columns, and fall back to the basic query if the
   database has not had the newer migration yet. */
async function getSafe(table, rich, basic) {
  try { return await get(table, rich); }
  catch (e) {
    console.log('  ' + table.padEnd(22) + 'newer columns missing \u2014 run schema.sql; using basics');
    return get(table, basic);
  }
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
    getSafe('tiers', 'select=slug,name,rank,price_ugx,caps&order=rank',
                     'select=slug,name,rank,price_ugx&order=rank'),
    get('ad_slots', 'select=key,label,size')
  ]);

  const oldTax = existing('taxonomy.json') || {};
  const oldCats = bySlug(oldTax.categories);
  const oldTiers = bySlug(oldTax.tiers);

  write('taxonomy.json', Object.assign({}, oldTax, {
    /* Keep the committed order and homepage flags; take names from the
       database so a rename in Supabase still reaches the site. */
    categories: (oldTax.categories && oldTax.categories.length
      ? oldTax.categories.map(c => {
          const db = cats.find(x => x.slug === c.slug);
          return db ? Object.assign({}, c, { name: db.name || c.name }) : c;
        })
      /* Deliberately NOT appending categories that exist only in the
         database: an old seed left a second, differently-named set there,
         which is where "Quantity Surveyors" and "Quantity Surveying"
         appearing side by side came from. The 22 committed categories are
         the list; the database can rename them, not add to them. */
      : cats),
    districts: dists.length ? dists : (oldTax.districts || []),
    accreditations: accs.length ? accs : (oldTax.accreditations || []),
    tiers: tiers.map(t => {
      const old = oldTiers[t.slug] || {};
      const dbCaps = t.caps && Object.keys(t.caps).length ? t.caps : null;
      return { slug: t.slug, name: t.name, rank: t.rank, price: t.price_ugx,
               caps: dbCaps || old.caps || {} };
    })
  }));

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
    featured: !!f.featured,
    featuredSort: f.featured_sort || 0,
    accreditations: (f.firm_accreditations || []).map(r => r.accreditations.slug),
    phone: f.phone || '',
    whatsapp: f.whatsapp || f.phone || '',
    email: f.email || '',
    website: f.website || '',
    logo: f.logo_url || '',
    catalogue: f.catalogue_url || '',
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
  const reviews = await getAll('reviews',
    'select=firm_id,rating,author_name,body,was_customer,firm_reply,replied_at,created_at' +
    '&status=eq.published&order=created_at.desc');

  /* The newest 20 published reviews go onto each profile. The reviewer's
     email is never selected, and names are shortened to "Grace N." */
  const shortName = n => {
    const p = String(n || '').trim().split(/\s+/);
    return p.length > 1 ? p[0] + ' ' + p[p.length - 1][0].toUpperCase() + '.' : (p[0] || 'Anonymous');
  };
  const listByFirm = {};
  reviews.forEach(r => {
    (listByFirm[r.firm_id] = listByFirm[r.firm_id] || []);
    if (listByFirm[r.firm_id].length < 20) listByFirm[r.firm_id].push({
      author: shortName(r.author_name), rating: r.rating, body: r.body,
      customer: !!r.was_customer, date: String(r.created_at || '').slice(0, 10),
      reply: r.firm_reply || '', replyDate: String(r.replied_at || '').slice(0, 10)
    });
  });
  /* firmJson ids are 1, 2, 3 \u2026 not database ids, so match by position */
  firms.forEach((f, i) => { firmJson[i].reviewList = listByFirm[f.id] || []; });
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
  const oldTenders = bySlug(existing('tenders.json'), 'ref');
  write('tenders.json', tenders.map(t => {
    const old = oldTenders[t.ref] || {};
    return {
      ref: t.ref, title: t.title, org: t.org, deadline: t.deadline,
      value: t.value_text, valueUgx: t.value_ugx, category: t.category,
      clientType: t.client_type || old.clientType || '',
      orgWebsite: t.org_website || old.orgWebsite || '',
      summary: t.summary || old.summary || '',
      featured: t.featured, source: t.source, postedAt: t.posted_at
    };
  }));

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
      link: a.link, active: a.active,
        weight: a.weight || 1,
        linkType: a.link_type || (a.link ? 'website' : 'none'),
        firmSlug: a.firm_slug || '', start: a.starts_on, end: a.ends_on
    }))
  });

  /* ── Monthly slots and the digest sponsor ────────────────── */
  try {
    const spots = await get('spotlight', 'select=*&active=is.true&order=month.desc');
    const oldSpot = existing('spotlight.json') || {};
    const pick = slot => {
      const r = spots.find(x => x.slot === slot);
      if (!r) return oldSpot[slot] || null;
      return {
        active: r.active, month: r.month, monthLabel: r.month_label || '',
        sponsored: slot !== 'project' && !!r.sponsored, advertiser: r.advertiser || '',
        name: r.name, tagline: r.tagline || '', body: r.body || '',
        image: r.image_url || '', alt: r.alt || '', link: r.link || '', cta: r.cta || '',
        location: r.location || '', sector: r.sector || '', completed: r.completed || '',
        credit: r.credit || '', specs: r.specs || [], facts: r.facts || [], lessons: r.lessons || []
      };
    };
    write('spotlight.json', Object.assign({}, oldSpot, {
      product: pick('product'), project: pick('project'), newsletter: pick('newsletter')
    }));
  } catch (e) { console.log('  spotlight.json         kept committed copy (' + e.message.slice(0, 60) + ')'); }

  /* ── Legal pages edited in the portal ────────────────────── */
  try {
    const legal = await get('legal_docs', 'select=key,effective,body,updated_at');
    if (legal.length) write('legal.json', Object.fromEntries(legal.map(d =>
      [d.key, { effective: d.effective, body: d.body, updated: d.updated_at }])));
  } catch (e) { console.log('  legal.json             none yet \u2014 shipped pages stay'); }

  console.log('\n  Pull complete. build.js will now generate pages from this data.\n');
}

main().catch(err => {
  console.error('\n  PULL FAILED: ' + err.message);
  console.error('  Keeping the existing data/*.json so the build still succeeds.');
  console.error('  The site will deploy with the last known good data.\n');
  process.exit(0);   // deliberately not a failure — a stale site beats no site
});
