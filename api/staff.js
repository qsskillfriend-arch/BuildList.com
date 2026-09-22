/* Vercel wrapper. Logic lives in lib/staff-core.js. */
import { handleStaff, bearer } from '../lib/staff-core.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false, error: 'Use POST' });
  }
  const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
  const out = await handleStaff(bearer(req.headers.authorization), body);
  return res.status(out.status).json(out.body);
}
