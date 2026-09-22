/* ═══════════════════════════════════════════════════════════════
   STAFF CORE
   BuildList.com — a product of Sharplink Ventures (U) Limited

   Inviting somebody creates a login, and creating a login needs the
   service-role key. That key bypasses every security policy, so it
   lives only in the host's environment and only this function uses it
   — after proving the caller is an administrator.

   Changing a role or removing somebody does not come through here:
   the staff table's own row-level security already lets an admin do
   that directly, so there is no reason to route it past a secret.
   ═══════════════════════════════════════════════════════════════ */

const ROLES = ['admin', 'editor', 'agent'];
const emailOk = e => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(e || ''));

async function whoIsAsking(token) {
  const url = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
  const service = process.env.SUPABASE_SERVICE_KEY;
  if (!url || !service || !token) return null;

  const me = await fetch(`${url}/auth/v1/user`, {
    headers: { Authorization: `Bearer ${token}`, apikey: process.env.SUPABASE_ANON_KEY || service }
  });
  if (!me.ok) return null;
  const user = await me.json();
  if (!user || !user.id) return null;

  const r = await fetch(`${url}/rest/v1/staff?user_id=eq.${user.id}&select=role,name`, {
    headers: { apikey: service, Authorization: `Bearer ${service}` }
  });
  if (!r.ok) return null;
  const rows = await r.json();
  return rows.length ? { id: user.id, email: user.email, role: rows[0].role } : null;
}

export async function handleStaff(token, body = {}) {
  const url = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
  const service = process.env.SUPABASE_SERVICE_KEY;
  if (!url || !service) {
    return { status: 200, body: { ok: false,
      message: 'SUPABASE_SERVICE_KEY is not set on the host, so invitations cannot be sent. ' +
               'Add it as a secret environment variable and redeploy.' } };
  }

  const caller = await whoIsAsking(token);
  if (!caller) return { status: 401, body: { ok: false, error: 'Sign in first.' } };
  if (caller.role !== 'admin') return { status: 403, body: { ok: false, error: 'Only an administrator can invite staff.' } };

  const email = String(body.email || '').trim().toLowerCase();
  const name = String(body.name || '').trim().slice(0, 80);
  const role = String(body.role || '');
  if (!emailOk(email)) return { status: 400, body: { ok: false, error: 'That email address does not look right.' } };
  if (!name) return { status: 400, body: { ok: false, error: 'Give their name, so the team list is readable.' } };
  if (!ROLES.includes(role)) return { status: 400, body: { ok: false, error: 'Unknown role.' } };

  const H = { apikey: service, Authorization: `Bearer ${service}`, 'Content-Type': 'application/json' };

  /* Invite: Supabase emails them a link to set their own password, so
     nobody ever has to send a password over WhatsApp. */
  const redirect = (process.env.SITE_URL || '').replace(/\/$/, '') + '/portal.html';
  const inv = await fetch(`${url}/auth/v1/invite`, {
    method: 'POST', headers: H,
    body: JSON.stringify({ email, data: { name }, redirect_to: redirect || undefined })
  });
  const invBody = await inv.json().catch(() => ({}));
  let userId = invBody && (invBody.id || (invBody.user && invBody.user.id));

  /* Already has an account: find it rather than failing. */
  if (!inv.ok) {
    const list = await fetch(`${url}/auth/v1/admin/users?per_page=1000`, { headers: H });
    const all = await list.json().catch(() => ({}));
    const found = (all.users || []).find(u => (u.email || '').toLowerCase() === email);
    if (!found) return { status: 200, body: { ok: false,
      message: 'Supabase refused the invitation: ' + (invBody.msg || invBody.message || inv.status) } };
    userId = found.id;
  }

  const ins = await fetch(`${url}/rest/v1/staff?on_conflict=user_id`, {
    method: 'POST',
    headers: Object.assign({}, H, { Prefer: 'resolution=merge-duplicates,return=representation' }),
    body: JSON.stringify({ user_id: userId, role, name, email })
  });
  if (!ins.ok) {
    return { status: 200, body: { ok: false,
      message: 'The login was created but adding them to staff failed: ' + (await ins.text()).slice(0, 160) } };
  }

  console.log('[staff] %s invited %s as %s', caller.email, email, role);
  return { status: 200, body: { ok: true, userId,
    message: inv.ok
      ? 'Invitation sent to ' + email + '. They set their own password from the email.'
      : email + ' already had an account, so they were added to staff directly.' } };
}

export function bearer(h) {
  h = String(h || '');
  return h.toLowerCase().startsWith('bearer ') ? h.slice(7).trim() : '';
}
