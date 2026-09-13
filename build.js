#!/usr/bin/env node
/* ═══════════════════════════════════════════════════════════════
   BUILDLIST — STATIC PAGE BUILDER  (Stage 5)
   A product of Sharplink Ventures (U) Limited

   The problem this solves: the app is hash-routed, so Google sees
   one page. A directory competing for a handful of keywords instead
   of thousands is a brochure, not a traffic engine.

   This generates a real HTML file per firm, per category, per
   category+district, per tender and per article — each with its own
   title, description, canonical URL and structured data. Visitors
   land on a page that is readable before any JavaScript runs, then
   continue into the app.

   No dependencies. No framework. Node 18+.

       node build.js

   Netlify: set the build command to `node build.js`, publish `.`
   ═══════════════════════════════════════════════════════════════ */

const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const SITE_URL = (process.env.SITE_URL || 'https://buildlist.com').replace(/\/$/, '');
const OUT_DIRS = ['firms', 'tenders', 'news', 'browse'];

const read = f => JSON.parse(fs.readFileSync(path.join(ROOT, 'data', f + '.json'), 'utf8'));
const D = {
  taxonomy: read('taxonomy'), firms: read('firms'), tenders: read('tenders'),
  jobs: read('jobs'), articles: read('articles'), prices: read('prices')
};

const esc = s => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

const catName  = s => (D.taxonomy.categories.find(c => c.slug === s) || {}).name || s;
const distName = s => (D.taxonomy.districts.find(d => d.slug === s) || {}).name || s;
const accName  = s => (D.taxonomy.accreditations.find(a => a.slug === s) || {}).name || s;
const tierName = s => (D.taxonomy.tiers.find(t => t.slug === s) || {}).name || s;
const tierRank = s => { const t = D.taxonomy.tiers.find(x => x.slug === s); return t ? t.rank : 99; };

const liveFirms = D.firms.filter(f => (f.status || 'live') !== 'pending' && (f.status || 'live') !== 'rejected');
const openTenders = D.tenders.filter(t => new Date(t.deadline) >= new Date());

/* Only fields worth a page get one. A category with no firms would be
   a thin page, which is worse for ranking than no page at all. */
const MIN_FOR_PAGE = 1;

/* Remove previously generated pages before rebuilding. Without this a
   renamed slug leaves an orphan page on disk that Google may already
   have indexed, and you end up with two URLs for one firm. Netlify
   builds in a clean checkout anyway; this keeps local builds honest. */
function clean() {
  OUT_DIRS.forEach(d => {
    const p = path.join(ROOT, d);
    if (fs.existsSync(p)) fs.rmSync(p, { recursive: true, force: true });
  });
}
clean();

let written = 0;
function write(rel, html) {
  const file = path.join(ROOT, rel);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, html);
  written++;
}

/* ── Shared chrome ──────────────────────────────────────────── */
const STYLE = `
*{margin:0;padding:0;box-sizing:border-box}
:root{--forest:#1A3C2A;--forest-d:#12261A;--gold:#C49A16;--parchment:#F8F6F1;
 --white:#fff;--border:#E3DFD5;--slate:#3D4A42;--muted:#7A857D;--r:10px}
body{font-family:Inter,system-ui,-apple-system,sans-serif;background:var(--parchment);
 color:#1E2A23;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--forest)}
.wrap{max-width:1080px;margin:0 auto;padding:0 22px}
header{background:var(--forest);padding:14px 0}
header .wrap{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.logo{color:#fff;font-weight:700;font-size:1.05rem;text-decoration:none;letter-spacing:-.015em;
 display:flex;align-items:center;gap:11px}
.logo-tile{width:40px;height:40px;background:var(--gold);border-radius:8px;display:flex;
 align-items:center;justify-content:center;flex-shrink:0}
.logo-tile svg{width:24px;height:24px}
.logo .tld{color:var(--gold)}
.logo small{display:block;font-size:.62rem;color:var(--gold);letter-spacing:.08em;font-weight:600;margin-top:1px}
header nav{margin-left:auto;display:flex;gap:16px;flex-wrap:wrap}
header nav a{color:rgba(255,255,255,.82);text-decoration:none;font-size:.86rem}
header nav a:hover{color:var(--gold)}
.crumb{padding:14px 0;font-size:.8rem;color:var(--muted)}
.crumb a{color:var(--muted)}
.hero{background:var(--forest-d);color:#fff;padding:34px 0}
.hero h1{font-size:1.9rem;line-height:1.2;margin-bottom:8px;font-weight:700;letter-spacing:-.01em}
.hero p{color:rgba(255,255,255,.72);max-width:62ch}
main{padding:30px 0 60px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.card{background:var(--white);border:1px solid var(--border);border-radius:var(--r);padding:18px}
.card.p{border-color:rgba(196,154,22,.5)}
.card h3{font-size:1rem;margin-bottom:3px}
.card h3 a{text-decoration:none}
.card .c{font-size:.78rem;color:var(--muted);margin-bottom:9px}
.card p{font-size:.86rem;color:var(--slate);margin-bottom:11px}
.meta{display:flex;gap:10px;font-size:.78rem;color:var(--muted);flex-wrap:wrap;
 padding-top:10px;border-top:1px solid var(--border)}
.badge{display:inline-block;font-size:.68rem;font-weight:700;padding:2px 8px;border-radius:12px;
 background:#F3EFE2;color:#8A6B10}
.tag{display:inline-block;font-size:.72rem;background:#EEF3EF;color:var(--forest);
 padding:2px 8px;border-radius:12px;margin:0 4px 4px 0}
.sec{background:var(--white);border:1px solid var(--border);border-radius:var(--r);
 padding:22px;margin-bottom:16px}
.sec h2{font-size:1.05rem;margin-bottom:12px}
.two{display:grid;grid-template-columns:1.7fr 1fr;gap:18px;align-items:start}
.btn{display:inline-block;background:var(--gold);color:var(--forest-d);padding:9px 17px;
 border-radius:8px;text-decoration:none;font-weight:600;font-size:.88rem}
.btn.o{background:transparent;border:1.5px solid var(--border);color:var(--forest)}
.links{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.links a{background:var(--white);border:1px solid var(--border);border-radius:20px;
 padding:5px 13px;font-size:.82rem;text-decoration:none}
.links a:hover{border-color:var(--forest)}
.note{font-size:.78rem;color:var(--muted);line-height:1.55}
footer{background:var(--forest-d);color:rgba(255,255,255,.55);padding:26px 0;font-size:.8rem}
footer a{color:rgba(255,255,255,.72)}
@media(max-width:760px){.two{grid-template-columns:1fr}.hero h1{font-size:1.45rem}}
`;

function page({ title, desc, canonical, crumbs, hero, body, jsonld }) {
  return `<!DOCTYPE html>
<html lang="en-UG">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<link rel="canonical" href="${canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:url" content="${canonical}">
<meta property="og:image" content="${SITE_URL}/og-image.png">
<meta property="og:site_name" content="BuildList.com">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>${STYLE}</style>
${jsonld ? `<script type="application/ld+json">${JSON.stringify(jsonld)}</script>` : ''}
</head>
<body>
<header><div class="wrap">
  <a class="logo" href="/">
    <span class="logo-tile"><svg viewBox="0 0 24 24" fill="none" stroke="#1A3C2A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 9 12 2 21 9 21 20 3 20 3 9"/><rect x="9" y="14" width="6" height="6"/></svg></span>
    <span>BuildList<span class="tld">.com</span><small>Uganda Construction Directory</small></span>
  </a>
  <nav>
    <a href="/">Home</a><a href="/browse/">Directory</a><a href="/#/tenders">Tenders</a>
    <a href="/#/jobs">Jobs</a><a href="/#/news">Prices</a><a href="/#/advertise">Advertise</a>
  </nav>
</div></header>
<div class="wrap"><div class="crumb">${crumbs}</div></div>
${hero ? `<div class="hero"><div class="wrap">${hero}</div></div>` : ''}
<main><div class="wrap">${body}</div></main>
<footer><div class="wrap">
  &copy; ${new Date().getFullYear()} BuildList.com &mdash; a product of Sharplink Ventures (U) Limited.
  Listings are cross-checked against the public ARB, ERB, SRB and URSB registers.
  Not affiliated with, or endorsed by, those bodies.
  <a href="/#/about">About</a> &middot;
  <a href="/#/privacy">Privacy</a> &middot;
  <a href="/#/terms">Terms</a>
</div></footer>
</body>
</html>`;
}

function firmCard(f) {
  return `<div class="card ${f.tier === 'platinum' ? 'p' : ''}">
    <h3><a href="/firms/${f.slug}/">${esc(f.name)}</a></h3>
    <div class="c">${f.categories.map(c => esc(catName(c))).join(' &middot; ')}</div>
    ${f.tier !== 'free' ? `<span class="badge">${esc(tierName(f.tier))}</span>` : ''}
    <p>${esc(f.desc)}</p>
    <div class="meta"><span>${esc(f.area)}</span>
    ${f.reviews ? `<span style="margin-left:auto">${f.rating} from ${f.reviews} reviews</span>` : ''}</div>
  </div>`;
}

/* ═══════════════ 1. FIRM PAGES ═══════════════ */
liveFirms.forEach(f => {
  const url = `${SITE_URL}/firms/${f.slug}/`;
  const cats = f.categories.map(catName).join(', ');
  const title = `${f.name} — ${cats} in ${distName(f.district)} | BuildList.com`;
  const desc = `${f.name}: ${cats.toLowerCase()} based in ${f.area}. ${f.desc}`.slice(0, 180);

  const ld = {
    '@context': 'https://schema.org', '@type': 'LocalBusiness',
    '@id': url, name: f.name, description: f.desc, url,
    address: { '@type': 'PostalAddress', streetAddress: f.area,
      addressLocality: distName(f.district), addressCountry: 'UG' },
    areaServed: distName(f.district)
  };
  if (f.phone) ld.telephone = f.phone;
  if (f.email) ld.email = f.email;
  if (f.logo) ld.image = `${SITE_URL}/${f.logo}`;
  if (f.lat && f.lng && f.geoPrecision === 'area')
    ld.geo = { '@type': 'GeoCoordinates', latitude: f.lat, longitude: f.lng };
  /* aggregateRating only when the reviews are real. Structured data
     claiming invented ratings is a Google manual-action risk, and a
     penalty is far harder to undo than to avoid. */
  if (f.reviews > 0 && f.rating > 0)
    ld.aggregateRating = { '@type': 'AggregateRating', ratingValue: f.rating,
      reviewCount: f.reviews, bestRating: 5 };

  const body = `<div class="two"><div>
    <div class="sec"><h2>About ${esc(f.name)}</h2><p>${esc(f.desc)}</p>
      ${f.established ? `<p class="note" style="margin-top:10px">Established ${f.established}${f.employees ? `, ${esc(f.employees)} staff` : ''}.</p>` : ''}
      <p class="note" style="margin-top:10px">${
        f.verified && f.verifiedDate
          ? `Verified ${new Date(f.verifiedDate).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })}. We telephoned this business, confirmed its premises and checked the relevant public register on that date. A verified badge is a record and contact check, not a guarantee of workmanship.`
          : f.descSource === 'submitted'
            ? 'Supplied by the business. These details were sent to us by the business itself and have not been independently checked.'
            : 'Compiled from public sources. We built this listing from public registers and directories; the business has not confirmed it yet, so details may be out of date. If this is your business you can correct or remove it at any time \u2014 <a href="/#/submit">tell us here</a>.'
      }</p></div>
    ${(f.services || []).length ? `<div class="sec"><h2>Services</h2>
      ${f.services.map(s => `<span class="tag">${esc(s)}</span>`).join('')}</div>` : ''}
    ${(f.photos || []).length ? `<div class="sec"><h2>Photographs</h2><div class="grid">
      ${f.photos.map(p => `<img src="/${esc(p.src)}" alt="${esc(p.alt)}" loading="lazy"
        style="width:100%;border-radius:8px;border:1px solid var(--border)">`).join('')}</div></div>` : ''}
    ${(f.projects || []).length ? `<div class="sec"><h2>Selected projects</h2>
      ${f.projects.map(p => `<div style="padding:9px 0;border-bottom:1px solid var(--border)">
        <b>${esc(p.name)}</b><div class="note">${p.year}${p.value ? ` &middot; ${esc(p.value)}` : ''}</div></div>`).join('')}</div>` : ''}
  </div><aside>
    <div class="sec"><h2>Contact</h2>
      <p class="note">${esc(f.area)}, ${esc(distName(f.district))}</p>
      ${f.phone ? `<p style="margin-top:9px"><a href="tel:${esc(f.phone)}">${esc(f.phone)}</a></p>` : ''}
      ${f.email ? `<p><a href="mailto:${esc(f.email)}">${esc(f.email)}</a></p>` : ''}
      ${f.whatsapp ? `<p style="margin-top:12px"><a class="btn" href="https://wa.me/${String(f.whatsapp).replace(/\D/g, '')}">Message on WhatsApp</a></p>` : ''}
      <p style="margin-top:9px"><a class="btn o" href="/#/firms/${f.slug}">Open in the directory</a></p>
    </div>
    ${(f.accreditations || []).length ? `<div class="sec"><h2>Accreditation</h2>
      ${f.accreditations.map(a => `<span class="tag">${esc(accName(a))}</span>`).join('')}
      <p class="note" style="margin-top:9px">Checked against the relevant public register.</p></div>` : ''}
    <div class="sec"><h2>Is this your business?</h2>
      <p class="note">Claim the listing to update details, add photographs and see how many people contacted you.</p>
      <p style="margin-top:10px"><a class="btn o" href="/#/submit">Claim listing</a></p></div>
  </aside></div>`;

  write(`firms/${f.slug}/index.html`, page({
    title, desc, canonical: url,
    crumbs: `<a href="/">Home</a> / <a href="/browse/">Directory</a> / ${esc(f.name)}`,
    hero: `<h1>${esc(f.name)}</h1><p>${esc(cats)} in ${esc(f.area)}</p>`,
    body, jsonld: ld
  }));
});

/* ═══════════════ 2. CATEGORY + CATEGORY×DISTRICT PAGES ═══════════════
   These are the money pages. Nobody searches "BuildList.com";
   they search "quantity surveyor Kampala".
   ════════════════════════════════════════════════════════════════ */
const comboLinks = [];

D.taxonomy.categories.forEach(cat => {
  const inCat = liveFirms.filter(f => f.categories.includes(cat.slug))
    .sort((a, b) => tierRank(a.tier) - tierRank(b.tier) || b.rating - a.rating);
  if (inCat.length < MIN_FOR_PAGE) return;

  const url = `${SITE_URL}/browse/${cat.slug}/`;
  comboLinks.push({ href: `/browse/${cat.slug}/`, label: `${cat.name} in Uganda`, n: inCat.length });

  const districts = [...new Set(inCat.map(f => f.district))];
  write(`browse/${cat.slug}/index.html`, page({
    title: `${cat.name} in Uganda — ${inCat.length} listed ${inCat.length === 1 ? 'firm' : 'firms'} | BuildList.com`,
    desc: `Find ${cat.name.toLowerCase()} in Uganda. ${inCat.length} listed ${inCat.length === 1 ? 'firm' : 'firms'} with contact details, location and accreditation, checked against the public registers.`,
    canonical: url,
    crumbs: `<a href="/">Home</a> / <a href="/browse/">Directory</a> / ${esc(cat.name)}`,
    hero: `<h1>${esc(cat.name)} in Uganda</h1><p>${inCat.length} listed ${inCat.length === 1 ? 'firm' : 'firms'}. Paid listings appear first and are labelled.</p>`,
    body: `<div class="grid">${inCat.map(firmCard).join('')}</div>
      ${districts.length > 1 ? `<div class="sec" style="margin-top:22px"><h2>By district</h2><div class="links">
        ${districts.map(d => `<a href="/browse/${cat.slug}-${d}/">${esc(cat.name)} in ${esc(distName(d))}</a>`).join('')}
      </div></div>` : ''}`,
    jsonld: {
      '@context': 'https://schema.org', '@type': 'CollectionPage',
      name: `${cat.name} in Uganda`, url,
      mainEntity: { '@type': 'ItemList', numberOfItems: inCat.length,
        itemListElement: inCat.slice(0, 25).map((f, i) => ({
          '@type': 'ListItem', position: i + 1, url: `${SITE_URL}/firms/${f.slug}/`, name: f.name })) }
    }
  }));

  districts.forEach(d => {
    const inBoth = inCat.filter(f => f.district === d);
    if (inBoth.length < MIN_FOR_PAGE) return;
    const slug = `${cat.slug}-${d}`;
    const u = `${SITE_URL}/browse/${slug}/`;
    comboLinks.push({ href: `/browse/${slug}/`, label: `${cat.name} in ${distName(d)}`, n: inBoth.length });
    write(`browse/${slug}/index.html`, page({
      title: `${cat.name} in ${distName(d)} — ${inBoth.length} listed | BuildList.com`,
      desc: `${cat.name} in ${distName(d)}, Uganda. ${inBoth.length} listed ${inBoth.length === 1 ? 'firm' : 'firms'} with phone numbers, locations and accreditation.`,
      canonical: u,
      crumbs: `<a href="/">Home</a> / <a href="/browse/">Directory</a> / <a href="/browse/${cat.slug}/">${esc(cat.name)}</a> / ${esc(distName(d))}`,
      hero: `<h1>${esc(cat.name)} in ${esc(distName(d))}</h1><p>${inBoth.length} listed ${inBoth.length === 1 ? 'firm' : 'firms'}.</p>`,
      body: `<div class="grid">${inBoth.map(firmCard).join('')}</div>
        <div class="sec" style="margin-top:22px"><h2>Related</h2><div class="links">
          <a href="/browse/${cat.slug}/">All ${esc(cat.name.toLowerCase())} in Uganda</a>
        </div></div>`,
      jsonld: { '@context': 'https://schema.org', '@type': 'CollectionPage',
        name: `${cat.name} in ${distName(d)}`, url: u }
    }));
  });
});

/* ═══════════════ 3. DIRECTORY INDEX ═══════════════ */
write('browse/index.html', page({
  title: `Construction directory for Uganda — firms, consultants and suppliers | BuildList.com`,
  desc: `Browse ${liveFirms.length} construction firms, consultants and material suppliers across Uganda by category and district.`,
  canonical: `${SITE_URL}/browse/`,
  crumbs: `<a href="/">Home</a> / Directory`,
  hero: `<h1>Uganda construction directory</h1><p>${liveFirms.length} listed ${liveFirms.length === 1 ? 'firm' : 'firms'} across ${new Set(liveFirms.map(f => f.district)).size} districts.</p>`,
  body: `<div class="sec"><h2>Browse by category and area</h2>
    <div class="links">${comboLinks.map(l => `<a href="${l.href}">${esc(l.label)} (${l.n})</a>`).join('')}</div>
    <p class="note" style="margin-top:14px">Prefer to search and filter? <a href="/#/directory">Open the interactive directory</a>.</p></div>
    <div class="grid" style="margin-top:18px">${liveFirms
      .sort((a, b) => tierRank(a.tier) - tierRank(b.tier) || b.rating - a.rating)
      .map(firmCard).join('')}</div>`
}));

/* ═══════════════ 4. TENDER PAGES ═══════════════ */
openTenders.forEach(t => {
  const slug = String(t.ref || t.title).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 70);
  const url = `${SITE_URL}/tenders/${slug}/`;
  const days = Math.ceil((new Date(t.deadline) - new Date()) / 86400000);
  write(`tenders/${slug}/index.html`, page({
    title: `${t.title} — ${t.org} | Tender notice | BuildList.com`,
    desc: `${t.org} tender: ${t.title}. Reference ${t.ref}. Closes ${t.deadline}. Estimated value ${t.value}.`.slice(0, 180),
    canonical: url,
    crumbs: `<a href="/">Home</a> / <a href="/#/tenders">Tenders</a> / ${esc(t.ref || '')}`,
    hero: `<h1>${esc(t.title)}</h1><p>${esc(t.org)}</p>`,
    body: `<div class="sec">
      <p><b>Reference</b><br>${esc(t.ref)}</p>
      <p style="margin-top:11px"><b>Estimated value</b><br>${esc(t.value)}</p>
      <p style="margin-top:11px"><b>Closing date</b><br>${esc(t.deadline)} (${days} day${days === 1 ? '' : 's'} remaining)</p>
      <p style="margin-top:11px"><b>Source</b><br>${esc(t.source || '')}</p>
      <p class="note" style="margin-top:16px">BuildList.com publishes tender notices for information.
      Always confirm details and submission requirements with the procuring entity before bidding.</p>
      <p style="margin-top:14px"><a class="btn" href="/#/tenders">See all open tenders</a></p></div>`,
    jsonld: { '@context': 'https://schema.org', '@type': 'WebPage', name: t.title, url }
  }));
});

/* ═══════════════ 5. ARTICLE PAGES ═══════════════ */
D.articles.forEach(a => {
  const url = `${SITE_URL}/news/${a.slug}/`;
  write(`news/${a.slug}/index.html`, page({
    title: `${a.title} | BuildList.com`,
    desc: String(a.excerpt).slice(0, 180),
    canonical: url,
    crumbs: `<a href="/">Home</a> / <a href="/#/news">News</a> / ${esc(a.category)}`,
    hero: `<h1>${esc(a.title)}</h1><p>${esc(a.category)} &middot; ${esc(a.date)}</p>`,
    body: `<div class="sec"><p>${esc(a.excerpt)}</p>
      ${a.body ? `<div style="margin-top:14px">${a.body}</div>` : ''}
      ${a.sponsored ? '<p class="note" style="margin-top:14px"><b>This is sponsored content, paid for by an advertiser.</b></p>' : ''}
      <p style="margin-top:16px"><a class="btn o" href="/#/news">More industry news</a></p></div>`,
    jsonld: { '@context': 'https://schema.org', '@type': 'Article', headline: a.title,
      description: a.excerpt, datePublished: a.date, url,
      publisher: { '@type': 'Organization', name: 'Sharplink Ventures (U) Limited' } }
  }));
});

/* ═══════════════ 6. SITEMAP ═══════════════ */
const urls = [
  { loc: `${SITE_URL}/`, pri: '1.0', freq: 'daily' },
  { loc: `${SITE_URL}/browse/`, pri: '0.95', freq: 'daily' },
  { loc: `${SITE_URL}/privacy`, pri: '0.3', freq: 'yearly' },
  { loc: `${SITE_URL}/terms`, pri: '0.3', freq: 'yearly' },
  ...comboLinks.map(l => ({ loc: SITE_URL + l.href, pri: '0.9', freq: 'weekly' })),
  ...liveFirms.map(f => ({ loc: `${SITE_URL}/firms/${f.slug}/`, pri: '0.8', freq: 'weekly' })),
  ...openTenders.map(t => ({ loc: `${SITE_URL}/tenders/${String(t.ref || t.title).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 70)}/`, pri: '0.7', freq: 'daily' })),
  ...D.articles.map(a => ({ loc: `${SITE_URL}/news/${a.slug}/`, pri: '0.6', freq: 'monthly' }))
];
const stamp = new Date().toISOString().slice(0, 10);
fs.writeFileSync(path.join(ROOT, 'sitemap.xml'),
`<?xml version="1.0" encoding="UTF-8"?>
<!-- Generated by build.js. Do not edit by hand; it is overwritten on every build. -->
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map(u => `  <url><loc>${u.loc}</loc><lastmod>${stamp}</lastmod><changefreq>${u.freq}</changefreq><priority>${u.pri}</priority></url>`).join('\n')}
</urlset>
`);

/* ═══════════════ 7. REDIRECTS ═══════════════
   The short category URLs are generated from taxonomy.json, so they can
   never drift from the pages that actually exist. Hand-written ones went
   stale the moment the categories changed, and a 301 to a 404 is worse
   than no redirect at all. */
const REDIRECT_MARK = '# ── BEGIN generated category shortcuts (build.js) ──';
const REDIRECT_END  = '# ── END generated category shortcuts ──';

const shortcuts = [REDIRECT_MARK,
  '# Do not edit between these markers. Rewritten on every build.',
  '# /quantity-surveying-kampala  →  /browse/quantity-surveying-kampala/'];

D.taxonomy.categories.forEach(cat => {
  if (!fs.existsSync(path.join(ROOT, 'browse', cat.slug))) return;
  shortcuts.push(`/${cat.slug}*`.padEnd(34) + `/browse/${cat.slug}:splat`.padEnd(40) + '301');
});
shortcuts.push(REDIRECT_END);

const rPath = path.join(ROOT, '_redirects');
let redirects = fs.readFileSync(rPath, 'utf8');
const a = redirects.indexOf(REDIRECT_MARK);
const b = redirects.indexOf(REDIRECT_END);
if (a !== -1 && b !== -1) {
  redirects = redirects.slice(0, a) + shortcuts.join('\n') + redirects.slice(b + REDIRECT_END.length);
} else {
  // First run: insert above the catch-all so it cannot swallow them
  redirects = redirects.replace(/(# ── Catch-all)/, shortcuts.join('\n') + '\n\n$1');
}
fs.writeFileSync(rPath, redirects);

console.log(`Built ${written} pages + sitemap (${urls.length} URLs) for ${SITE_URL}`);
console.log(`  ${liveFirms.length} firms · ${comboLinks.length} category pages · ${openTenders.length} tenders · ${D.articles.length} articles`);
if (liveFirms.length < 50) {
  console.log('\nNote: with ' + liveFirms.length + ' firms this generates a thin site. The SEO');
  console.log('benefit of Stage 5 arrives around 300 listings. Keep collecting.');
}
