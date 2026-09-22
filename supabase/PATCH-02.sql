-- ═══════════════════════════════════════════════════════════════
-- PATCH 02 — bring the database in line with the site
-- BuildList.com, a product of Sharplink Ventures (U) Limited
--
-- Run once, after schema.sql. Safe to run again.
--
-- 1. CATEGORIES. An early seed created a second set of categories with
--    different slugs and names ("Architecture Firms", "Civil
--    Engineering" ...) alongside the site's own. That is where
--    duplicates such as "Quantity Surveyors" and "Quantity Surveying"
--    came from. This moves any firm filed under an old category to the
--    matching new one, removes the old set, and makes the 22 below the
--    only categories, with the names, order and homepage flags the site
--    uses.
-- 2. TIERS. Stores what each tier includes, so the portal's Tiers page
--    and the public site read the same thing.
-- ═══════════════════════════════════════════════════════════════

alter table categories add column if not exists on_home boolean not null default false;
alter table firms add column if not exists catalogue_url text;
alter table firms add column if not exists logo_url text;

-- ── 1a. The 22 categories, exactly as the site shows them ─────
insert into categories (slug, name, cluster, sort, on_home) values
  ('architecture-design', 'Architects & Designers', 'Design', 1, true),
  ('quantity-surveying', 'Quantity Surveyors', 'Professionals', 2, true),
  ('civil-structural', 'Civil & Structural Engineers', 'Professionals', 3, true),
  ('land-surveying', 'Land Surveyors', 'Professionals', 4, true),
  ('property-valuers', 'Property Valuers', 'Professionals', 5, true),
  ('urban-planning', 'Urban & Town Planners', 'Professionals', 6, false),
  ('general-contracting', 'General Contractors', 'Contractors', 7, true),
  ('electrical-contracting', 'Electrical Contractors', 'Contractors', 8, true),
  ('suppliers', 'Material Suppliers', 'Supply', 9, true),
  ('plumbing-fire', 'Plumbing & Fire Fighting', 'Contractors', 10, true),
  ('plant-hire', 'Plant & Equipment Hire', 'Trades', 11, false),
  ('hvac', 'Heating, Ventilation & Air Conditioning', 'Contractors', 12, true),
  ('structural-steel', 'Aluminium, Steel & Glass Works', 'Contractors', 13, true),
  ('interior-design', 'Interior Designers', 'Trades', 14, false),
  ('landscaping', 'Landscaping & External Works', 'Contractors', 15, false),
  ('building-management', 'Building Management Systems', 'Services', 16, false),
  ('ict-network', 'ICT & Networks Specialists', 'Services', 17, false),
  ('facility-management', 'Facility Managers', 'Services', 18, false),
  ('health-safety', 'Health & Safety Consultants', 'Services', 19, false),
  ('environmental', 'Environmental & Sustainability', 'Services', 20, false),
  ('real-estate-development', 'Real Estate Developers', 'Development', 21, false),
  ('tradesmen', 'Tradesmen', 'Trades', 22, true)
on conflict (slug) do update set
  name = excluded.name, cluster = excluded.cluster,
  sort = excluded.sort, on_home = excluded.on_home;

-- ── 1b. Re-file firms from the old slugs to the new ones ──────
with map(old_slug, new_slug) as (values
  ('quantity-surveyors','quantity-surveying'),
  ('architecture-firms','architecture-design'),
  ('civil-engineering','civil-structural'),
  ('structural-engineering','civil-structural'),
  ('me-engineering','electrical-contracting'),
  ('land-surveyors','land-surveying'),
  ('building-contractors','general-contracting'),
  ('road-contractors','general-contracting'),
  ('material-suppliers','suppliers'),
  ('plant-equipment-hire','plant-hire'),
  ('interior-designers','interior-design'),
  ('office-furniture','suppliers')
)
insert into firm_categories (firm_id, category_id)
select fc.firm_id, nc.id
from firm_categories fc
join categories oc on oc.id = fc.category_id
join map m on m.old_slug = oc.slug
join categories nc on nc.slug = m.new_slug
on conflict do nothing;

-- ── 1c. Remove every category that is not one of the 22 ───────
delete from firm_categories where category_id in
  (select id from categories where slug not in ('architecture-design', 'quantity-surveying', 'civil-structural', 'land-surveying', 'property-valuers', 'urban-planning', 'general-contracting', 'electrical-contracting', 'suppliers', 'plumbing-fire', 'plant-hire', 'hvac', 'structural-steel', 'interior-design', 'landscaping', 'building-management', 'ict-network', 'facility-management', 'health-safety', 'environmental', 'real-estate-development', 'tradesmen'));
delete from categories where slug not in ('architecture-design', 'quantity-surveying', 'civil-structural', 'land-surveying', 'property-valuers', 'urban-planning', 'general-contracting', 'electrical-contracting', 'suppliers', 'plumbing-fire', 'plant-hire', 'hvac', 'structural-steel', 'interior-design', 'landscaping', 'building-management', 'ict-network', 'facility-management', 'health-safety', 'environmental', 'real-estate-development', 'tradesmen');

-- ── 2. Tier capabilities and prices ───────────────────────────
alter table tiers add column if not exists caps jsonb default '{}'::jsonb;
update tiers set caps = '{"photos": 100, "logo": true, "whatsapp": true, "website": true, "descriptionChars": 5000, "services": 50, "projects": 30, "video": true, "preciseMap": true, "badge": true, "sortBoost": 4, "homepageFeature": true, "leadAlerts": true, "monthlyReport": true, "catalogue": true, "categories": 6, "reviewReply": true}'::jsonb, price_ugx = 1500000 where slug = 'platinum';
update tiers set caps = '{"photos": 25, "logo": true, "whatsapp": true, "website": true, "descriptionChars": 2500, "services": 25, "projects": 12, "video": true, "preciseMap": true, "badge": true, "sortBoost": 3, "homepageFeature": false, "leadAlerts": true, "monthlyReport": true, "catalogue": true, "categories": 4, "reviewReply": true}'::jsonb, price_ugx = 400000 where slug = 'premium';
update tiers set caps = '{"photos": 10, "logo": true, "whatsapp": true, "website": true, "descriptionChars": 1200, "services": 12, "projects": 4, "video": false, "preciseMap": true, "badge": true, "sortBoost": 2, "homepageFeature": false, "leadAlerts": true, "monthlyReport": false, "catalogue": true, "categories": 3, "reviewReply": true}'::jsonb, price_ugx = 150000 where slug = 'verified';
update tiers set caps = '{"photos": 4, "logo": true, "whatsapp": true, "website": true, "descriptionChars": 600, "services": 6, "projects": 0, "video": false, "preciseMap": true, "badge": false, "sortBoost": 1, "homepageFeature": false, "leadAlerts": false, "monthlyReport": false, "catalogue": false, "categories": 2, "reviewReply": false}'::jsonb, price_ugx = 50000 where slug = 'starter';
update tiers set caps = '{"photos": 0, "logo": false, "whatsapp": false, "website": false, "descriptionChars": 160, "services": 0, "projects": 0, "video": false, "preciseMap": false, "badge": false, "sortBoost": 0, "homepageFeature": false, "leadAlerts": false, "monthlyReport": false, "catalogue": false, "categories": 1, "reviewReply": false}'::jsonb, price_ugx = 0 where slug = 'free';

-- ── 3. Reviews come only through the site's server ────────────
-- The original policy let anyone insert a review straight from a browser
-- with the public key, skipping every check. Reviews now go through
-- /api/form, which validates them, ties them to a real listing and allows
-- one per email per firm. The service key it uses is not affected by RLS.
drop policy if exists "anyone submits a review" on reviews;

-- A firm's public reply, shown only on tiers that include replying.
alter table reviews add column if not exists reject_reason text;

-- Check: should read 22, then five rows each with caps filled
select count(*) as categories from categories;
select slug, price_ugx, jsonb_typeof(caps) = 'object' and caps <> '{}'::jsonb as caps_set
from tiers order by price_ugx;
