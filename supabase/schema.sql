-- ═══════════════════════════════════════════════════════════════
-- BUILDLIST — SUPABASE SCHEMA
-- A product of Sharplink Ventures (U) Limited
--
-- Run this once in the Supabase SQL editor:
--   Dashboard → SQL Editor → New query → paste → Run
--
-- Read supabase/README.md first. In particular: free-tier projects
-- PAUSE after 7 days of inactivity and go offline until someone
-- manually restores them. Budget the paid tier before real firms
-- depend on this.
-- ═══════════════════════════════════════════════════════════════

-- ── Reference tables ──────────────────────────────────────────
create table if not exists categories (
  id      serial primary key,
  slug    text unique not null,
  name    text not null,
  cluster text,
  sort    int default 0
);

create table if not exists districts (
  id   serial primary key,
  slug text unique not null,
  name text not null
);

create table if not exists accreditations (
  id   serial primary key,
  slug text unique not null,
  name text not null
);

create table if not exists tiers (
  slug       text primary key,
  name       text not null,
  rank       int  not null,           -- 0 = highest. Drives default search order.
  price_ugx  bigint not null default 0
);

-- ── Firms ─────────────────────────────────────────────────────
create table if not exists firms (
  id            uuid primary key default gen_random_uuid(),
  slug          text unique not null,
  name          text not null,
  initials      text,
  description   text,
  district      text not null references districts(slug),
  area          text,

  phone         text,
  whatsapp      text,
  email         text,
  website       text,

  logo_url      text,

  tier          text not null default 'free' references tiers(slug),
  status        text not null default 'pending'
                check (status in ('pending','live','rejected','suspended')),

  verified      boolean not null default false,
  verified_at   date,
  verified_by   uuid references auth.users,

  boraqs_no     text,
  uipe_no       text,
  ursb_no       text,
  tin           text,

  -- Ownership and disclosure. is_group_company powers the visible
  -- "Group company" tag promised on the public About page.
  owner_id          uuid references auth.users,
  is_group_company  boolean not null default false,

  tier_expires_at   date,

  established   int,
  employees     text,

  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index if not exists firms_status_idx   on firms(status);
create index if not exists firms_district_idx on firms(district);
create index if not exists firms_tier_idx     on firms(tier);
create index if not exists firms_owner_idx    on firms(owner_id);

-- Full-text search over the fields people actually type
create index if not exists firms_search_idx on firms
  using gin (to_tsvector('english', coalesce(name,'') || ' ' || coalesce(description,'') || ' ' || coalesce(area,'')));

create table if not exists firm_categories (
  firm_id     uuid references firms on delete cascade,
  category_id int  references categories on delete cascade,
  primary key (firm_id, category_id)
);

create table if not exists firm_accreditations (
  firm_id           uuid references firms on delete cascade,
  accreditation_id  int  references accreditations on delete cascade,
  primary key (firm_id, accreditation_id)
);

create table if not exists firm_services (
  id      bigserial primary key,
  firm_id uuid references firms on delete cascade,
  label   text not null,
  sort    int default 0
);

create table if not exists firm_photos (
  id       bigserial primary key,
  firm_id  uuid references firms on delete cascade,
  url      text not null,
  alt      text,
  caption  text,
  sort     int default 0
);

create table if not exists firm_projects (
  id       bigserial primary key,
  firm_id  uuid references firms on delete cascade,
  name     text not null,
  value    text,
  year     int
);

-- ── Reviews ───────────────────────────────────────────────────
create table if not exists reviews (
  id            uuid primary key default gen_random_uuid(),
  firm_id       uuid references firms on delete cascade,
  author_name   text not null,
  author_email  text not null,
  rating        int  not null check (rating between 1 and 5),
  body          text not null,
  was_customer  boolean not null default false,
  status        text not null default 'pending'
                check (status in ('pending','published','rejected')),
  firm_reply    text,
  replied_at    timestamptz,
  moderated_by  uuid references auth.users,
  created_at    timestamptz not null default now()
);
create index if not exists reviews_firm_idx on reviews(firm_id, status);

-- ── Tenders and jobs ──────────────────────────────────────────
create table if not exists tenders (
  id         uuid primary key default gen_random_uuid(),
  ref        text,
  title      text not null,
  org        text,
  category   text,
  deadline   date not null,
  value_text text,
  value_ugx  bigint,
  featured   boolean not null default false,
  source     text,
  posted_at  date not null default current_date,
  created_at timestamptz not null default now()
);
create index if not exists tenders_deadline_idx on tenders(deadline);

create table if not exists jobs (
  id           uuid primary key default gen_random_uuid(),
  slug         text unique not null,
  title        text not null,
  company      text,
  company_id   uuid references firms on delete set null,
  district     text references districts(slug),
  location     text,
  employment   text,
  discipline   text,
  salary       text,
  experience   text,
  level        text check (level in ('entry','mid','senior','principal')),
  apply_email  text,
  featured     boolean not null default false,
  posted_at    date not null default current_date,
  closes_at    date,
  created_at   timestamptz not null default now()
);
create index if not exists jobs_closes_idx on jobs(closes_at);

-- ── Articles and prices ───────────────────────────────────────
create table if not exists articles (
  id         uuid primary key default gen_random_uuid(),
  slug       text unique not null,
  title      text not null,
  excerpt    text,
  body       text,
  category   text,
  icon       text,
  sponsored  boolean not null default false,
  published  boolean not null default true,
  read_time  text,
  published_at date not null default current_date,
  created_at timestamptz not null default now()
);

create table if not exists price_snapshots (
  id          bigserial primary key,
  collected_on date not null,
  sources     text[],
  note        text,
  created_at  timestamptz not null default now(),
  unique (collected_on)
);

create table if not exists price_items (
  id          bigserial primary key,
  snapshot_id bigint references price_snapshots on delete cascade,
  material    text not null,
  value_text  text not null,
  change_text text,
  direction   text check (direction in ('up','down','flat'))
);
-- Keeping snapshots rather than overwriting is what turns a price
-- table into a time series — and the time series is a sellable product.

-- ── Advertising ───────────────────────────────────────────────
create table if not exists ad_slots (
  key    text primary key,
  label  text not null,
  size   text,
  rate_ugx bigint
);

create table if not exists ads (
  id          uuid primary key default gen_random_uuid(),
  campaign_id text unique not null,
  slot        text not null references ad_slots(key),
  advertiser  text not null,
  image_url   text,
  alt         text,
  title       text,
  body        text,
  cta         text,
  link        text not null,
  active      boolean not null default true,
  starts_on   date,
  ends_on     date,
  created_at  timestamptz not null default now()
);
create index if not exists ads_slot_idx on ads(slot, active, starts_on, ends_on);

create table if not exists ad_events (
  id         bigserial primary key,
  ad_id      uuid references ads on delete cascade,
  kind       text not null check (kind in ('impression','click')),
  occurred_at timestamptz not null default now()
);

-- ── Listing analytics ─────────────────────────────────────────
-- The table the whole sales strategy rests on: "your listing was
-- viewed 46 times last month and 11 people tapped your number."
create table if not exists listing_events (
  id          bigserial primary key,
  firm_id     uuid references firms on delete cascade,
  kind        text not null check (kind in ('view','contact_whatsapp','contact_phone','contact_email','share')),
  occurred_at timestamptz not null default now()
);
create index if not exists listing_events_idx on listing_events(firm_id, occurred_at);

create or replace view firm_monthly_stats as
select firm_id,
       date_trunc('month', occurred_at) as month,
       count(*) filter (where kind = 'view')     as views,
       count(*) filter (where kind like 'contact%') as contacts
from listing_events
group by firm_id, date_trunc('month', occurred_at);

-- ── Payments ──────────────────────────────────────────────────
create table if not exists payments (
  id           uuid primary key default gen_random_uuid(),
  firm_id      uuid references firms on delete set null,
  tier         text references tiers(slug),
  amount_ugx   bigint not null,
  provider     text check (provider in ('flutterwave','pesapal','manual','bank')),
  provider_ref text,
  status       text not null default 'pending'
               check (status in ('pending','paid','failed','refunded')),
  paid_at      timestamptz,
  period_start date,
  period_end   date,
  created_at   timestamptz not null default now()
);
create index if not exists payments_firm_idx on payments(firm_id, status);

-- ── Admin roles ───────────────────────────────────────────────
create table if not exists staff (
  user_id uuid primary key references auth.users on delete cascade,
  role    text not null check (role in ('admin','editor','agent')),
  name    text
);

create or replace function is_staff() returns boolean as $$
  select exists (select 1 from staff where user_id = auth.uid());
$$ language sql security definer stable;

create or replace function is_admin() returns boolean as $$
  select exists (select 1 from staff where user_id = auth.uid() and role = 'admin');
$$ language sql security definer stable;

-- ═══════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY
--
-- Get this right or the whole revenue model is bypassable from the
-- browser console. A firm must never be able to set its own tier,
-- verified flag or status.
-- ═══════════════════════════════════════════════════════════════
alter table firms          enable row level security;
alter table reviews        enable row level security;
alter table listing_events enable row level security;
alter table payments       enable row level security;
alter table ads            enable row level security;
alter table staff          enable row level security;

-- Public reads only live listings
drop policy if exists "public reads live firms" on firms;
create policy "public reads live firms" on firms
  for select using (status = 'live');

-- An owner sees their own record whatever its status
drop policy if exists "owner reads own firm" on firms;
create policy "owner reads own firm" on firms
  for select using (auth.uid() = owner_id);

-- An owner may edit their own record, but NOT the commercial fields
drop policy if exists "owner updates own firm" on firms;
create policy "owner updates own firm" on firms
  for update using (auth.uid() = owner_id)
  with check (auth.uid() = owner_id);

-- Belt and braces: a trigger enforces the commercial fields even if a
-- policy is later loosened by mistake.
create or replace function guard_firm_commercial_fields()
returns trigger as $$
begin
  if is_staff() then
    return new;
  end if;
  new.tier             := old.tier;
  new.status           := old.status;
  new.verified         := old.verified;
  new.verified_at      := old.verified_at;
  new.verified_by      := old.verified_by;
  new.tier_expires_at  := old.tier_expires_at;
  new.is_group_company := old.is_group_company;
  new.owner_id         := old.owner_id;
  new.updated_at       := now();
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists firms_guard on firms;
create trigger firms_guard before update on firms
  for each row execute function guard_firm_commercial_fields();

-- Staff can do anything to firms
drop policy if exists "staff manage firms" on firms;
create policy "staff manage firms" on firms
  for all using (is_staff()) with check (is_staff());

-- Reviews: public sees published only; anyone may submit as pending
drop policy if exists "public reads published reviews" on reviews;
create policy "public reads published reviews" on reviews
  for select using (status = 'published');

drop policy if exists "anyone submits a review" on reviews;
create policy "anyone submits a review" on reviews
  for insert with check (status = 'pending');

drop policy if exists "staff moderate reviews" on reviews;
create policy "staff moderate reviews" on reviews
  for all using (is_staff()) with check (is_staff());

-- Listing events: anyone may write one, only staff and the owner read
drop policy if exists "anyone logs an event" on listing_events;
create policy "anyone logs an event" on listing_events
  for insert with check (true);

drop policy if exists "owner reads own events" on listing_events;
create policy "owner reads own events" on listing_events
  for select using (
    is_staff() or exists (select 1 from firms f where f.id = firm_id and f.owner_id = auth.uid())
  );

-- Payments: owner reads own, staff manage
drop policy if exists "owner reads own payments" on payments;
create policy "owner reads own payments" on payments
  for select using (
    is_staff() or exists (select 1 from firms f where f.id = firm_id and f.owner_id = auth.uid())
  );

drop policy if exists "staff manage payments" on payments;
create policy "staff manage payments" on payments
  for all using (is_staff()) with check (is_staff());

-- Ads: public reads live campaigns, staff manage
drop policy if exists "public reads live ads" on ads;
create policy "public reads live ads" on ads
  for select using (
    active and (starts_on is null or starts_on <= current_date)
           and (ends_on   is null or ends_on   >= current_date)
  );

drop policy if exists "staff manage ads" on ads;
create policy "staff manage ads" on ads
  for all using (is_staff()) with check (is_staff());

-- Staff table: only admins may change it, staff may read it
drop policy if exists "staff read staff" on staff;
create policy "staff read staff" on staff for select using (is_staff());

drop policy if exists "admins manage staff" on staff;
create policy "admins manage staff" on staff
  for all using (is_admin()) with check (is_admin());

-- Reference tables are world-readable, staff-writable
alter table categories     enable row level security;
alter table districts      enable row level security;
alter table accreditations enable row level security;
alter table tiers          enable row level security;
alter table ad_slots       enable row level security;

do $$
declare t text;
begin
  foreach t in array array['categories','districts','accreditations','tiers','ad_slots'] loop
    execute format('drop policy if exists "public reads %1$s" on %1$s', t);
    execute format('create policy "public reads %1$s" on %1$s for select using (true)', t);
    execute format('drop policy if exists "staff writes %1$s" on %1$s', t);
    execute format('create policy "staff writes %1$s" on %1$s for all using (is_staff()) with check (is_staff())', t);
  end loop;
end $$;

-- ── Media library ─────────────────────────────────────────────
-- Images are resized in the browser before upload, so each record
-- points at several widths of the same picture and the site serves
-- whichever fits the reader's screen.
create table if not exists media (
  id         uuid primary key default gen_random_uuid(),
  base       text not null,
  target     text,                -- which slot it was uploaded for
  natural_w  int,
  natural_h  int,
  variants   jsonb not null,      -- [{width,height,name,bytes}]
  urls       jsonb not null,      -- {"400": "...", "800": "...", "1600": "..."}
  alt        text,
  uploaded_by uuid references auth.users,
  created_at timestamptz not null default now()
);
create index if not exists media_target_idx on media(target, created_at desc);

alter table media enable row level security;
drop policy if exists "public reads media" on media;
create policy "public reads media" on media for select using (true);
drop policy if exists "staff writes media" on media;
create policy "staff writes media" on media
  for all using (is_staff()) with check (is_staff());

-- Articles gain a body and a publish switch. Taking something down
-- hides it; it is never deleted, so it can always be restored.
alter table articles add column if not exists body text;
alter table articles add column if not exists published boolean not null default true;
create index if not exists articles_published_idx on articles(published, published_at desc);

-- ── Storage buckets ───────────────────────────────────────────
-- Run these in the Storage section, or via SQL:
insert into storage.buckets (id, name, public)
  values ('logos','logos',true), ('firm-photos','firm-photos',true),
         ('ad-creatives','ad-creatives',true), ('media','media',true)
  on conflict (id) do nothing;

-- Anyone may read; only staff and the firm's owner may write
drop policy if exists "public reads images" on storage.objects;
create policy "public reads images" on storage.objects
  for select using (bucket_id in ('logos','firm-photos','ad-creatives','media'));

drop policy if exists "staff writes images" on storage.objects;
create policy "staff writes images" on storage.objects
  for all using (bucket_id in ('logos','firm-photos','ad-creatives','media') and is_staff())
  with check (bucket_id in ('logos','firm-photos','ad-creatives','media') and is_staff());

-- ── Make yourself an admin ────────────────────────────────────
-- 1. Create your account: Authentication → Users → Add user
-- 2. Copy its UUID, then run:
--    insert into staff (user_id, role, name)
--    values ('PASTE-UUID-HERE', 'admin', 'Your Name');
