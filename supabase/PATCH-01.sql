-- ═══════════════════════════════════════════════════════════════
-- PATCH 01 — run this if you already created your tables
-- BuildList.com, a product of Sharplink Ventures (U) Limited
--
-- Two fixes:
--   1. Row-level security on six tables that had none. Without it,
--      anyone holding the anon key — which is published in the
--      browser by design — could post a fake tender or vacancy.
--   2. A unique key on tenders.ref, so migrate.js can be run twice
--      without inserting a second copy of every notice.
--
-- Safe to run more than once. If you have not created your tables
-- yet, just run the full schema.sql instead; it already includes
-- everything here.
-- ═══════════════════════════════════════════════════════════════

do $$
declare t text;
begin
  foreach t in array array['tenders','jobs','articles','price_snapshots','price_items'] loop
    execute format('alter table %I enable row level security', t);
    execute format('drop policy if exists "public reads %1$s" on %1$I', t);
    execute format('create policy "public reads %1$s" on %1$I for select using (true)', t);
    execute format('drop policy if exists "staff writes %1$s" on %1$I', t);
    execute format('create policy "staff writes %1$s" on %1$I
      for all using (is_staff()) with check (is_staff())', t);
  end loop;
end $$;

-- A taken-down article must not be readable by the public
drop policy if exists "public reads articles" on articles;
create policy "public reads articles" on articles
  for select using (published or is_staff());

alter table ad_events enable row level security;
drop policy if exists "anyone logs an ad event" on ad_events;
create policy "anyone logs an ad event" on ad_events
  for insert with check (true);
drop policy if exists "staff read ad events" on ad_events;
create policy "staff read ad events" on ad_events
  for select using (is_staff());

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'tenders_ref_key') then
    alter table tenders add constraint tenders_ref_key unique (ref);
  end if;
end $$;

-- Check it worked: every row below should say true.
select relname as table_name, relrowsecurity as rls_enabled
from pg_class
where relname in ('tenders','jobs','articles','price_snapshots','price_items','ad_events')
order by relname;

-- ═══════════════════════════════════════════════════════════════
-- TWO-FACTOR: require it where it actually matters
--
-- The portal asks an administrator for a code, but a UI prompt is a
-- courtesy. This makes it a control: the commercial columns can only
-- be written by a session that proved a second factor (aal2).
--
-- Run this only AFTER at least one administrator has enrolled, or you
-- will lock yourself out of your own tier and approval controls.
-- ═══════════════════════════════════════════════════════════════

create or replace function is_aal2()
returns boolean as $$
  select coalesce(
    (auth.jwt() ->> 'aal') = 'aal2',
    false);
$$ language sql stable;

-- Example: uncomment once you have enrolled, to require a second
-- factor before anyone can change money or staff.
--
-- drop policy if exists "staff manage ads" on ads;
-- create policy "staff manage ads" on ads
--   for all using (is_admin() and is_aal2())
--   with check (is_admin() and is_aal2());
--
-- drop policy if exists "admin manages staff" on staff;
-- create policy "admin manages staff" on staff
--   for all using (is_admin() and is_aal2())
--   with check (is_admin() and is_aal2());
