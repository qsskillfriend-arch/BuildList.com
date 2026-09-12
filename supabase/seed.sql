-- ═══════════════════════════════════════════════════════════════
-- SEED: reference data only.
-- Run AFTER schema.sql. This loads categories, districts,
-- accreditations, tiers and ad slots — the same values currently in
-- data/taxonomy.json and data/ads.json, so nothing shifts underneath
-- the public site when you migrate.
--
-- It does NOT load firms. Move those with the migration script in
-- supabase/README.md, after you have replaced the sample records.
-- ═══════════════════════════════════════════════════════════════

insert into tiers (slug,name,rank,price_ugx) values
  ('platinum','Platinum',0,1500000),
  ('premium','Premium',1,400000),
  ('verified','Verified',2,150000),
  ('starter','Starter',3,50000),
  ('free','Free',4,0)
on conflict (slug) do update set name=excluded.name, rank=excluded.rank, price_ugx=excluded.price_ugx;

insert into districts (slug,name) values
  ('kampala','Kampala'),('wakiso','Wakiso'),('mukono','Mukono'),('jinja','Jinja'),
  ('entebbe','Entebbe'),('mbarara','Mbarara'),('gulu','Gulu'),('mbale','Mbale')
on conflict (slug) do nothing;

insert into categories (slug,name,cluster,sort) values
  ('quantity-surveyors','Quantity Surveyors','Professionals',1),
  ('architecture-firms','Architecture Firms','Professionals',2),
  ('civil-engineering','Civil Engineering','Professionals',3),
  ('structural-engineering','Structural Engineering','Professionals',4),
  ('me-engineering','M&E Engineering','Professionals',5),
  ('land-surveyors','Land Surveyors','Professionals',6),
  ('building-contractors','Building Contractors','Contractors',7),
  ('road-contractors','Road Contractors','Contractors',8),
  ('material-suppliers','Material Suppliers','Suppliers',9),
  ('plant-equipment-hire','Plant & Equipment Hire','Services',10),
  ('interior-designers','Interior Designers','Furnishings',11),
  ('office-furniture','Office Furniture','Furnishings',12)
on conflict (slug) do nothing;

insert into accreditations (slug,name) values
  ('boraqs','BORAQS Registered'),('uipe','UIPE Member'),('uiqs','UIQS Member'),
  ('ncic','NCIC Registered'),('iso','ISO Certified'),('ppda','PPDA Listed')
on conflict (slug) do nothing;

insert into ad_slots (key,label,size,rate_ugx) values
  ('home-leaderboard','Homepage leaderboard','970x90',2000000),
  ('home-billboard','Homepage billboard','970x250',2500000),
  ('home-lower','Homepage lower leaderboard','970x90',1200000),
  ('directory-strip','Directory top strip','970x90',1200000),
  ('directory-sidebar','Directory sidebar','300x250',800000),
  ('directory-infeed','Directory in-feed','text',600000),
  ('tenders-leaderboard','Tenders board leaderboard','970x90',1200000),
  ('tenders-infeed','Tenders in-feed','text',600000),
  ('tenders-sidebar','Tenders sidebar','300x250',600000),
  ('tenders-sidebar-b','Tenders sidebar lower','300x250',450000),
  ('jobs-leaderboard','Jobs board leaderboard','970x90',900000),
  ('jobs-sidebar','Jobs sidebar','300x250',500000),
  ('news-sidebar','News sidebar','300x250',500000),
  ('footer-leaderboard','Footer leaderboard','728x90',400000)
on conflict (key) do update set label=excluded.label, size=excluded.size;
