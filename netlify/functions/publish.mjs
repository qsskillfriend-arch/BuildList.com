/* Netlify wrapper. Same core as the Vercel handler. */
import { handlePublish, bearer } from '../../lib/publish-core.js';

export default async (request) => {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ ok: false, error: 'Use POST' }), {
      status: 405, headers: { 'Content-Type': 'application/json', Allow: 'POST' }
    });
  }
  const out = await handlePublish(bearer(request.headers.get('authorization')));
  return new Response(JSON.stringify(out.body), {
    status: out.status, headers: { 'Content-Type': 'application/json' }
  });
};

export const config = { path: '/api/publish' };
