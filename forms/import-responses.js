#!/usr/bin/env node
/* ═══════════════════════════════════════════════════════════════
   BUILDLIST.COM — FORM RESPONSES → LISTINGS
   Turns the Google Form responses CSV into records you can paste
   into data/firms.json, or import through the admin dashboard.

     node forms/import-responses.js responses.csv

   Writes forms/new-listings.json and prints a summary.

   It refuses to import anyone who did not give permission to publish,
   and flags duplicates against your existing 618 listings rather than
   silently creating two pages for the same business.
   ═══════════════════════════════════════════════════════════════ */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const csvPath = process.argv[2];
if (!csvPath) {
  console.error('Usage: node forms/import-responses.js <responses.csv>');
  process.exit(1);
}

/* ── Minimal CSV parser: handles quoted fields and embedded commas ── */
function parseCsv(text) {
  const rows = [];
  let row = [], field = '', inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') inQuotes = false;
      else field += c;
    } else if (c === '"') inQuotes = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
    else if (c !== '\r') field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows.filter(r => r.some(v => v.trim()));
}

const raw = fs.readFileSync(csvPath, 'utf8');
const rows = parseCsv(raw);
const header = rows[0].map(h => h.trim());
const records = rows.slice(1).map(r => {
  const o = {};
  header.forEach((h, i) => { o[h] = (r[i] || '').trim(); });
  return o;
});

/* ── Load existing data so we map onto the real taxonomy ── */
const tax = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/taxonomy.json'), 'utf8'));
const existing = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/firms.json'), 'utf8'));

const catBySlug = {};
tax.categories.forEach(c => { catBySlug[c.name.toLowerCase()] = c.slug; });
const accBySlug = {};
tax.accreditations.forEach(a => { accBySlug[a.name.toLowerCase()] = a.slug; });
const districtSlugs = new Set(tax.districts.map(d => d.slug));

const col = name => header.find(h => h.toLowerCase().startsWith(name.toLowerCase())) || name;
const F = {
  ts:        col('Timestamp'),
  name:      col('Business name'),
  cat:       col('What does your business do'),
  moreCats:  col('Any other categories'),
  desc:      col('In one or two sentences'),
  services:  col('Main services or products'),
  district:  col('District'),
  area:      col('Area, trading centre'),
  landmark:  col('Nearest landmark'),
  phone:     col('Phone number'),
  whatsapp:  col('WhatsApp number'),
  email:     col('Email address'),
  website:   col('Website or Facebook'),
  contact:   col('Your name'),
  role:      col('Your role'),
  year:      col('Year the business started'),
  staff:     col('How many people work'),
  accs:      col('Are you registered with any'),
  regNo:     col('Registration or membership number'),
  logo:      col('Do you have a logo'),
  photos:    col('Photographs of your shop'),
  consent:   col('Do you give BuildList.com permission'),
  callPref:  col('Can we call you'),
  digest:    col('May we send you our weekly digest'),
  colEmail1: col('Colleague 1 — email address'),
  colName1:  col('Colleague 1 — name and role'),
  colEmail2: col('Colleague 2 — email address'),
  colName2:  col('Colleague 2 — name and role'),
  colEmail3: col('Colleague 3 — email address'),
  colName3:  col('Colleague 3 — name and role'),
  colKnow:   col('Do these colleagues know'),
  notes:     col('Anything else'),
  referrer:  col('Who told you about BuildList')
};

const slugify = s => String(s)
  .replace(/\(.*?\)/g, ' ').toLowerCase().replace(/&/g, ' and ')
  .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  .replace(/-(ltd|limited|co|company|u|uganda)$/, '').slice(0, 70).replace(/^-|-$/g, '');

const cleanPhone = p => {
  let v = String(p || '').replace(/[^\d+]/g, '');
  if (v.startsWith('0') && v.length >= 9) v = '+256' + v.slice(1);
  if (v.startsWith('256')) v = '+' + v;
  return v.startsWith('+') ? v : '';
};

const norm = s => String(s || '').toLowerCase().replace(/[^a-z0-9]/g, '');
const isEmail = e => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(e || '').trim());

/* Everyone who should receive the digest, in one place. Nominated
   colleagues are held separately from the business's own address
   because they need a confirm-or-ignore message first — we are not
   adding somebody to a mailing list on a third party's say-so. */
const digestList = [];

const out = [];
const unmappedLog = [];
const badEmails = [];
const skipped = { noConsent: [], noName: [], noPhone: [], duplicate: [] };
let nextId = Math.max(0, ...existing.map(f => f.id || 0));
const usedSlugs = new Set(existing.map(f => f.slug));
const existingByName = new Map(existing.map(f => [norm(f.name), f]));
const existingByPhone = new Map(existing.filter(f => f.phone).map(f => [f.phone, f]));

records.forEach(r => {
  const name = r[F.name];
  if (!name) { skipped.noName.push('(blank row)'); return; }

  /* Consent is not optional. Publishing a business that ticked
     "no" is the thing that gets you a complaint and a takedown. */
  if (!/^yes/i.test(r[F.consent] || '')) { skipped.noConsent.push(name); return; }

  const phone = cleanPhone(r[F.phone]);
  if (!phone) { skipped.noPhone.push(name); return; }

  const dupe = existingByName.get(norm(name)) || existingByPhone.get(phone);
  if (dupe) { skipped.duplicate.push(name + '  →  already listed as "' + dupe.name + '"'); return; }

  let slug = slugify(name);
  let n = 1;
  while (usedSlugs.has(slug)) { n++; slug = slugify(name) + '-' + n; }
  usedSlugs.add(slug);

  const cats = [];
  const unmapped = [];
  const addCat = label => {
    const t = String(label || '').trim();
    if (!t || /^other/i.test(t)) return;
    const s = catBySlug[t.toLowerCase()];
    if (s) { if (!cats.includes(s)) cats.push(s); }
    else unmapped.push(t);
  };
  addCat(r[F.cat]);
  String(r[F.moreCats] || '').split(',').forEach(addCat);
  if (unmapped.length) unmappedLog.push(name + '  →  "' + unmapped.join('", "') + '"');

  const accs = String(r[F.accs] || '').split(',')
    .map(a => accBySlug[a.trim().toLowerCase()])
    .filter(Boolean);

  const district = districtSlugs.has(String(r[F.district]).toLowerCase())
    ? String(r[F.district]).toLowerCase() : 'kampala';

  const area = [r[F.area], r[F.district]].filter(Boolean).join(', ');

  /* Nominated colleagues for the weekly digest */
  const extras = [];
  [[F.colEmail1, F.colName1], [F.colEmail2, F.colName2], [F.colEmail3, F.colName3]]
    .forEach(pair => {
      const addr = String(r[pair[0]] || '').trim().toLowerCase();
      if (!isEmail(addr)) {
        if (addr) badEmails.push(name + '  →  "' + addr + '"');
        return;
      }
      extras.push({ email: addr, who: r[pair[1]] || '' });
    });
  extras.forEach(x => digestList.push({
    email: x.email,
    who: x.who,
    firm: name,
    nominatedBy: r[F.contact] || '',
    aware: /^yes/i.test(r[F.colKnow] || ''),
    status: 'awaiting-confirmation'
  }));
  // The business's own address, if they opted in themselves
  if (/^yes/i.test(r[F.digest] || '') && isEmail(r[F.email])) {
    digestList.push({
      email: String(r[F.email]).trim().toLowerCase(),
      who: r[F.contact] || '',
      firm: name,
      nominatedBy: 'self',
      aware: true,
      status: 'opted-in'
    });
  }

  out.push({
    id: ++nextId,
    slug,
    name,
    initials: name.split(/\s+/).filter(w => /^[A-Za-z]/.test(w)).slice(0, 2)
                  .map(w => w[0].toUpperCase()).join('') || '??',
    categories: cats.length ? cats : ['general-contracting'],
    _needsCategory: !cats.length,
    district,
    area,
    address: [r[F.area], r[F.landmark]].filter(Boolean).join(' — '),
    desc: r[F.desc] || '',
    descSource: 'submitted',
    services: String(r[F.services] || '').split(',').map(s => s.trim()).filter(Boolean),
    rating: 0,
    reviews: 0,
    tier: 'free',
    // Every submission starts pending. Somebody phones the number
    // before it appears on the site — that is what the verified
    // badge on your About page actually promises.
    status: 'pending',
    accreditations: accs,
    phone,
    whatsapp: cleanPhone(r[F.whatsapp]) || phone,
    email: /@/.test(r[F.email]) ? r[F.email].toLowerCase() : '',
    website: r[F.website] && !/^https?:/.test(r[F.website])
             ? 'https://' + r[F.website].replace(/^\/+/, '') : (r[F.website] || ''),
    logo: '',
    photos: [],
    projects: [],
    established: /^\d{4}$/.test(r[F.year]) ? Number(r[F.year]) : '',
    employees: r[F.staff] || '',
    verified: false,
    verifiedDate: null,
    createdAt: new Date(r[F.ts] || Date.now()).toISOString().slice(0, 10),
    lat: 0.3476, lng: 32.5825, geoPrecision: 'district',

    // Intake notes — useful in the admin, strip before publishing if you prefer
    _intake: {
      contactPerson: r[F.contact] || '',
      digestRecipients: extras,
      colleaguesAware: r[F.colKnow] || '',
      role: r[F.role] || '',
      regNumber: r[F.regNo] || '',
      logoPromised: /yes/i.test(r[F.logo] || ''),
      photosPromised: /yes/i.test(r[F.photos] || ''),
      photoVisitRequested: /send someone/i.test(r[F.photos] || ''),
      contactPreference: r[F.callPref] || '',
      digestOptIn: /yes/i.test(r[F.digest] || ''),
      referrer: r[F.referrer] || '',
      notes: r[F.notes] || ''
    }
  });
});

const outPath = path.join(__dirname, 'new-listings.json');
fs.writeFileSync(outPath, JSON.stringify(out, null, 2) + '\n');

/* Deduplicate the digest list — the same colleague may be nominated by
   two firms, and nobody should get two confirmation emails. */
const seenEmail = new Set();
const digestUnique = digestList.filter(d => {
  if (seenEmail.has(d.email)) return false;
  seenEmail.add(d.email); return true;
});
fs.writeFileSync(path.join(__dirname, 'digest-recipients.json'),
  JSON.stringify(digestUnique, null, 2) + '\n');

/* CSV for Brevo, MailerLite or whichever platform you use */
const csvRows = [['email', 'name', 'firm', 'nominated_by', 'status']]
  .concat(digestUnique.map(d => [d.email, d.who, d.firm, d.nominatedBy, d.status]
    .map(v => '"' + String(v).replace(/"/g, '""') + '"')));
fs.writeFileSync(path.join(__dirname, 'digest-recipients.csv'),
  csvRows.map(r => r.join(',')).join('\n') + '\n');

console.log('\n═══════════════════════════════════════════════');
console.log(' FORM IMPORT');
console.log('═══════════════════════════════════════════════');
console.log(' Submissions read      : ' + records.length);
console.log(' Ready to add          : ' + out.length + '  (status: pending)');
console.log(' Skipped — no consent  : ' + skipped.noConsent.length);
console.log(' Skipped — no phone    : ' + skipped.noPhone.length);
console.log(' Skipped — duplicates  : ' + skipped.duplicate.length);
console.log('');
if (skipped.noConsent.length) {
  console.log(' NO CONSENT (do not publish, but worth a follow-up call):');
  skipped.noConsent.forEach(n => console.log('   · ' + n));
  console.log('');
}
if (skipped.noPhone.length) {
  console.log(' NO USABLE PHONE (call them back and fix it):');
  skipped.noPhone.forEach(n => console.log('   · ' + n));
  console.log('');
}
if (skipped.duplicate.length) {
  console.log(' ALREADY IN THE DIRECTORY:');
  skipped.duplicate.forEach(n => console.log('   · ' + n));
  console.log('');
}
const needsCat = out.filter(f => f._needsCategory);
if (needsCat.length || unmappedLog.length) {
  console.log(' CATEGORY NEEDS A HUMAN:');
  console.log('  These did not match data/taxonomy.json and were parked in');
  console.log('  "General Contracting". Fix them in the admin before publishing,');
  console.log('  or they appear under the wrong filter.');
  unmappedLog.forEach(l => console.log('   · ' + l));
  needsCat.filter(f => !unmappedLog.some(l => l.startsWith(f.name)))
          .forEach(f => console.log('   · ' + f.name + '  →  (no category given)'));
  console.log('');
}
if (badEmails.length) {
  console.log(' COLLEAGUE EMAIL LOOKS WRONG (call and check):');
  badEmails.forEach(l => console.log('   · ' + l));
  console.log('');
}

const awaiting = digestUnique.filter(d => d.status === 'awaiting-confirmation');
const notAware = awaiting.filter(d => !d.aware);
console.log(' DIGEST LIST');
console.log('  Opted in themselves      : ' + digestUnique.filter(d => d.status === 'opted-in').length);
console.log('  Colleagues nominated     : ' + awaiting.length + '  (send confirmation first)');
console.log('  Of those, not yet told   : ' + notAware.length + '  (use the introduction wording)');
console.log('');
console.log(' Written to: forms/new-listings.json');
console.log('             forms/digest-recipients.json');
console.log('             forms/digest-recipients.csv   ← import to your mailing platform');
console.log('');
console.log(' NEXT STEP — phone every one of them before publishing.');
console.log(' Then paste the records into data/firms.json and set');
console.log(' status to "live" in the admin dashboard.');
console.log('═══════════════════════════════════════════════\n');

const photoVisits = out.filter(f => f._intake.photoVisitRequested);
if (photoVisits.length) {
  console.log(' ' + photoVisits.length + ' business(es) asked for a photography visit —');
  console.log(' that is a warm lead for a paid listing:');
  photoVisits.forEach(f => console.log('   · ' + f.name + '  ' + f.phone + '  ' + f.area));
  console.log('');
}
