/* Netlify function wrapper. Same core as the Vercel handler, so a
   submission behaves identically on either host. _redirects maps the
   public /api/form path here, which is why the browser never needs to
   know which platform it is talking to. */
import { handleSubmission, parseBody } from '../../lib/form-core.js';

export default async (request) => {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ ok: false, error: 'Use POST' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json', Allow: 'POST' }
    });
  }
  const raw = await request.text();
  const body = parseBody(raw, request.headers.get('content-type') || '');
  const headers = Object.fromEntries(request.headers.entries());
  const out = await handleSubmission(body, headers);
  return new Response(JSON.stringify(out.body), {
    status: out.status,
    headers: { 'Content-Type': 'application/json' }
  });
};

export const config = { path: '/api/form' };
