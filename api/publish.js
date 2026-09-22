/* Vercel wrapper. Logic lives in lib/publish-core.js so this and the
   Netlify function behave identically. */
import { handlePublish, bearer } from '../lib/publish-core.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false, error: 'Use POST' });
  }
  const out = await handlePublish(bearer(req.headers.authorization));
  return res.status(out.status).json(out.body);
}
