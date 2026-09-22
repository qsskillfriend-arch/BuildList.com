/* ═══════════════════════════════════════════════════════════════
   FORM CORE
   BuildList.com — a product of Sharplink Ventures (U) Limited

   The whole form-handling logic, kept platform-neutral so Vercel and
   Netlify run identical code. The two thin wrappers around it are:

     api/form.js                 Vercel serverless function
     netlify/functions/form.mjs  Netlify function

   Both expose the same public endpoint, /api/form, so the browser
   never needs to know which host it is on. Netlify maps that path to
   its function in _redirects; on Vercel it is the file path.

   Delivery is attempted in order and stops at the first that works:
     1. Supabase  SUPABASE_URL + SUPABASE_SERVICE_KEY  → submissions table
     2. Email     RESEND_API_KEY + FORM_NOTIFY_EMAIL
     3. Webhook   FORM_WEBHOOK_URL                      → Slack, Make, Zapier
     4. Logs      nothing configured                    → function log
   ═══════════════════════════════════════════════════════════════ */

export const FORMS = {
  /* Every <form name="..."> on the site must appear here, or the API
     rejects it with "Unknown form". A test checks the two lists match,
     because this list drifting out of step once already meant six forms
     silently failing. */
  'listing-submission':  { label: 'New listing application',       urgent: true  },
  'contact':             { label: 'Contact message',               urgent: true  },
  'newsletter':          { label: 'Digest subscription',           urgent: false },
  'tender-alerts':       { label: 'Tender alert signup',           urgent: false },
  'job-alerts':          { label: 'Job alert signup',              urgent: false },
  'quote-request':       { label: 'Quotation request',             urgent: true  },
  'event-submission':    { label: 'Event submission',              urgent: false },
  'tender-submission':   { label: 'Tender notice submitted',       urgent: true  },
  'job-submission':      { label: 'Vacancy submitted',             urgent: true  },
  'advertising-enquiry': { label: 'ADVERTISING ENQUIRY',           urgent: true  },
  'claim-listing':       { label: 'LISTING CLAIM',                 urgent: true  },
  /* The privacy policy promises 48 hours, and the law expects it. */
  'removal-request':     { label: 'REMOVAL REQUEST \u2014 48 HOURS', urgent: true  }
};

const MAX_FIELD = 4000;
const MAX_FIELDS = 40;

const clean = v => String(v == null ? '' : v).slice(0, MAX_FIELD).trim();

/* Submissions are shown back to staff in the portal, so anything that
   could be read as markup is neutralised here rather than relying on
   every future display site remembering to escape it. */
function sanitise(body) {
  const out = {};
  let n = 0;
  for (const [k, v] of Object.entries(body || {})) {
    if (n++ >= MAX_FIELDS) break;
    if (k === 'bot-field' || k === 'company-website') continue;
    out[k.slice(0, 64)] = clean(v).replace(/[<>]/g, '');
  }
  return out;
}

async function toSupabase(form, fields, meta) {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_KEY;
  if (!url || !key) return { ok: false, skipped: true };
  const res = await fetch(`${url.replace(/\/$/, '')}/rest/v1/submissions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      apikey: key,
      Authorization: `Bearer ${key}`,
      Prefer: 'return=minimal'
    },
    body: JSON.stringify({ form, fields, meta })
  });
  return { ok: res.ok, status: res.status };
}

async function toEmail(form, fields) {
  const key = process.env.RESEND_API_KEY;
  const to = process.env.FORM_NOTIFY_EMAIL;
  if (!key || !to) return { ok: false, skipped: true };
  const label = (FORMS[form] || {}).label || form;
  const rows = Object.entries(fields)
    .map(([k, v]) => `<tr><td style="padding:6px 14px 6px 0;color:#7A857D;font-size:13px">${k}</td>` +
                     `<td style="padding:6px 0;font-size:14px"><strong>${v || '—'}</strong></td></tr>`)
    .join('');
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${key}` },
    body: JSON.stringify({
      from: process.env.FORM_FROM_EMAIL || 'BuildList.com <onboarding@resend.dev>',
      to: to.split(',').map(s => s.trim()),
      subject: `${label} — BuildList.com`,
      html: `<div style="font-family:system-ui,sans-serif;max-width:560px">
        <h2 style="color:#1A3C2A;font-size:18px;margin:0 0 4px">${label}</h2>
        <p style="color:#7A857D;font-size:13px;margin:0 0 16px">via buildlist.com</p>
        <table style="border-collapse:collapse">${rows}</table></div>`
    })
  });
  return { ok: res.ok, status: res.status };
}

async function toWebhook(form, fields) {
  const url = process.env.FORM_WEBHOOK_URL;
  if (!url) return { ok: false, skipped: true };
  const label = (FORMS[form] || {}).label || form;
  const text = `*${label}*\n` + Object.entries(fields).map(([k, v]) => `• ${k}: ${v || '—'}`).join('\n');
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, form, fields })
  });
  return { ok: res.ok, status: res.status };
}

/**
 * Handle one submission.
 * @param {object} body    parsed request body
 * @param {object} headers request headers, lowercased keys
 * @returns {{status:number, body:object}}
 */
export async function handleSubmission(body = {}, headers = {}) {
  /* Honeypot. A person never fills a hidden field; a bot fills every
     field. Return success so the bot learns nothing from the response. */
  if (body['bot-field'] || body['company-website']) {
    return { status: 200, body: { ok: true, received: true } };
  }

  const form = clean(body['form-name'] || body.form);
  if (!form || !FORMS[form]) {
    return { status: 400, body: { ok: false, error: 'Unknown form' } };
  }

  const fields = sanitise(body);
  delete fields['form-name'];

  const meta = {
    at: new Date().toISOString(),
    ua: clean(headers['user-agent']).slice(0, 200),
    ref: clean(headers.referer || headers.referrer).slice(0, 200),
    /* Kept for rate limiting and abuse only. Never displayed. */
    ip: clean(headers['x-forwarded-for']).split(',')[0]
  };

  const results = {};
  for (const [name, fn] of [['db', toSupabase], ['email', toEmail], ['hook', toWebhook]]) {
    try { results[name] = await (name === 'db' ? fn(form, fields, meta) : fn(form, fields)); }
    catch (e) { results[name] = { ok: false, detail: e.message }; }
  }

  const stored = results.db.ok || results.email.ok || results.hook.ok;
  if (!stored) {
    /* Nothing configured, or everything failed. Log it so the
       submission exists somewhere, and say so rather than pretending
       it was filed. */
    console.log('[form] UNSTORED', form, JSON.stringify(fields), JSON.stringify(results));
  }

  return {
    status: 200,
    body: {
      ok: true,
      stored,
      form,
      message: stored
        ? 'Received.'
        : 'Received, but no delivery target is configured yet — check the function logs.'
    }
  };
}

/** Parse a body that may arrive as JSON, form-encoded, or already parsed. */
export function parseBody(raw, contentType = '') {
  if (raw && typeof raw === 'object') return raw;
  if (typeof raw !== 'string' || !raw) return {};
  if (contentType.includes('application/json')) {
    try { return JSON.parse(raw); } catch { /* fall through */ }
  }
  try { return JSON.parse(raw); }
  catch { return Object.fromEntries(new URLSearchParams(raw)); }
}
