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
  ('architecture-design','Architects & Designers','Design',1),
  ('quantity-surveying','Quantity Surveyors','Professionals',2),
  ('civil-structural','Civil & Structural Engineers','Professionals',3),
  ('land-surveying','Land Surveyors','Professionals',4),
  ('property-valuers','Property Valuers','Professionals',5),
  ('urban-planning','Urban & Town Planners','Professionals',6),
  ('general-contracting','General Contractors','Contractors',7),
  ('electrical-contracting','Electrical Contractors','Contractors',8),
  ('suppliers','Material Suppliers','Supply',9),
  ('plumbing-fire','Plumbing & Fire Fighting','Contractors',10),
  ('plant-hire','Plant & Equipment Hire','Trades',11),
  ('hvac','Heating, Ventilation & Air Conditioning','Contractors',12),
  ('structural-steel','Aluminium, Steel & Glass Works','Contractors',13),
  ('interior-design','Interior Designers','Trades',14),
  ('landscaping','Landscaping & External Works','Contractors',15),
  ('building-management','Building Management Systems','Services',16),
  ('ict-network','ICT & Networks Specialists','Services',17),
  ('facility-management','Facility Managers','Services',18),
  ('health-safety','Health & Safety Consultants','Services',19),
  ('environmental','Environmental & Sustainability','Services',20),
  ('real-estate-development','Real Estate Developers','Development',21),
  ('tradesmen','Tradesmen','Trades',22)
on conflict (slug) do update set name = excluded.name, cluster = excluded.cluster, sort = excluded.sort;

insert into accreditations (slug,name) values
  ('boraqs','ARB Registered'),('uipe','UIPE Member'),('uiqs','ISU Member'),
  ('ncic','ERB Registered'),('iso','ISO Certified'),('ppda','PPDA Listed')
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
