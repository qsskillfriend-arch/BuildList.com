/* ═══════════════════════════════════════════════════════════════
   PUBLISH CORE
   BuildList.com — a product of Sharplink Ventures (U) Limited

   Saving in the portal writes to Supabase. The public site is
   generated at build time, so nothing a visitor sees changes until a
   deploy runs. This is the button that runs one.

   Why it goes through a function rather than the browser calling the
   build hook directly: a build hook URL is a bearer token. Anyone who
   opened portal.html could read it, and then anyone on the internet
   could trigger your builds until the month's minutes were gone.

   So the URL lives in an environment variable, and this function only
   fires it after checking that the caller holds a valid Supabase
   session belonging to a row in the staff table.
   ═══════════════════════════════════════════════════════════════ */

/** Confirm the bearer token belongs to a member of staff. */
async function whoIsAsking(token) {
  const url = process.env.SUPABASE_URL;
  const service = process.env.SUPABASE_SERVICE_KEY;
  const anon = process.env.SUPABASE_ANON_KEY;
  if (!url || !token) return null;

  /* Ask Supabase who this token is. A forged token fails here. */
  const me = await fetch(`${url.replace(/\/$/, '')}/auth/v1/user`, {
    headers: { Authorization: `Bearer ${token}`, apikey: anon || service || '' }
  });
  if (!me.ok) return null;
  const user = await me.json();
  if (!user || !user.id) return null;

  /* Then check they are staff. Read with the service key so the answer
     does not depend on the very policies we are about to act under. */
  if (!service) return null;
  const staff = await fetch(
    `${url.replace(/\/$/, '')}/rest/v1/staff?user_id=eq.${user.id}&select=role,name`,
    { headers: { apikey: service, Authorization: `Bearer ${service}` } });
  if (!staff.ok) return null;
  const rows = await staff.json();
  if (!rows.length) return null;

  return { id: user.id, email: user.email, role: rows[0].role, name: rows[0].name };
}

export async function handlePublish(token) {
  const hook = process.env.BUILD_HOOK_URL;

  const person = await whoIsAsking(token);
  if (!person) {
    return { status: 401, body: { ok: false, error: 'Sign in as a member of staff first.' } };
  }

  if (!hook) {
    /* Say precisely what is missing. "Something went wrong" would send
       somebody looking in the wrong place for an afternoon. */
    return {
      status: 200,
      body: {
        ok: false,
        configured: false,
        message: 'No BUILD_HOOK_URL is set, so there is nothing to trigger. ' +
                 'Create a build hook in your host and add the URL as an environment variable. ' +
                 'Your changes are saved in the database either way and will appear at the next deploy.'
      }
    };
  }

  const res = await fetch(hook, { method: 'POST' });
  if (!res.ok) {
    return {
      status: 200,
      body: {
        ok: false, configured: true,
        message: 'The host refused the build request (' + res.status + '). ' +
                 'The hook URL may have been revoked. Nothing is lost — your changes are saved.'
      }
    };
  }

  console.log('[publish] triggered by', person.email, person.role);
  return {
    status: 200,
    body: {
      ok: true, configured: true,
      by: person.name || person.email,
      at: new Date().toISOString(),
      message: 'Build started. The site updates in about a minute.'
    }
  };
}

/** Pull the bearer token out of an Authorization header. */
export function bearer(header) {
  const h = String(header || '');
  return h.toLowerCase().startsWith('bearer ') ? h.slice(7).trim() : '';
}
