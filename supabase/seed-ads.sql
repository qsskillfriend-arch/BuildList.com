-- ═══════════════════════════════════════════════════════════════
-- SEED ROTATING ADS  —  6 placeholder campaigns per slot
-- BuildList.com, a product of Sharplink Ventures (U) Limited
--
-- Run AFTER schema.sql and seed.sql. Fills every slot with six rotating
-- placeholders so you can see rotation working before selling anything.
-- Safe to run more than once; matched on campaign_id.
-- ═══════════════════════════════════════════════════════════════

alter table ads add column if not exists weight int not null default 1;
alter table ads add column if not exists link_type text default 'website';
alter table ads add column if not exists firm_slug text;

-- 'link' was NOT NULL, from before an advert could legitimately have no
-- destination. Brand-awareness placement with link_type = 'none' is a
-- real product, so the column has to allow it.
alter table ads alter column link drop not null;

-- Slot registry. Keys name the page and position they sit in, so a
-- report can never credit an impression to the wrong page.
insert into ad_slots (key, label, size) values
  ('home-leaderboard', 'Homepage leaderboard', '970x90'),
  ('home-billboard', 'Homepage billboard', '970x250'),
  ('directory-sidebar', 'Directory sidebar', '300x250'),
  ('directory-infeed', 'Directory in-feed', 'text'),
  ('tenders-leaderboard', 'Tenders board leaderboard', '970x90'),
  ('tenders-infeed', 'Tenders in-feed', 'text'),
  ('tenders-sidebar', 'Tenders sidebar', '300x250'),
  ('jobs-leaderboard', 'Jobs top leaderboard', '970x90'),
  ('jobs-sidebar', 'Jobs sidebar', '300x250'),
  ('news-sidebar', 'News sidebar', '300x250'),
  ('footer-leaderboard', 'Footer leaderboard', '728x90'),
  ('jobs-sidebar-2', 'Jobs sidebar, second', '300x250'),
  ('jobs-sidebar-3', 'Jobs sidebar, third', '300x250'),
  ('news-leaderboard', 'News top leaderboard', '970x90'),
  ('news-sidebar-2', 'News sidebar, second', '300x250'),
  ('news-sidebar-3', 'News sidebar, third', '300x250'),
  ('tenders-sidebar-2', 'Tenders sidebar, second', '300x250'),
  ('tenders-sidebar-3', 'Tenders sidebar, third', '300x250')
on conflict (key) do update set label = excluded.label, size = excluded.size;

insert into ads (campaign_id, slot, advertiser, image_url, alt, link, link_type,
                 active, starts_on, ends_on, weight)
values
  ('home-leaderboard-sample-1', 'home-leaderboard', 'Sample Advertiser 1', 'images/ads/leaderboard-1.png', 'Placeholder creative 1 for the Homepage leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('home-leaderboard-sample-2', 'home-leaderboard', 'Sample Advertiser 2', 'images/ads/leaderboard-2.png', 'Placeholder creative 2 for the Homepage leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('home-leaderboard-sample-3', 'home-leaderboard', 'Sample Advertiser 3', 'images/ads/leaderboard-3.png', 'Placeholder creative 3 for the Homepage leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('home-leaderboard-sample-4', 'home-leaderboard', 'Sample Advertiser 4', 'images/ads/leaderboard-4.png', 'Placeholder creative 4 for the Homepage leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('home-leaderboard-sample-5', 'home-leaderboard', 'Sample Advertiser 5', 'images/ads/leaderboard-5.png', 'Placeholder creative 5 for the Homepage leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('home-leaderboard-sample-6', 'home-leaderboard', 'Sample Advertiser 6', 'images/ads/leaderboard-6.png', 'Placeholder creative 6 for the Homepage leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('home-billboard-sample-1', 'home-billboard', 'Sample Advertiser 1', 'images/ads/billboard-1.png', 'Placeholder creative 1 for the Homepage billboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('home-billboard-sample-2', 'home-billboard', 'Sample Advertiser 2', 'images/ads/billboard-2.png', 'Placeholder creative 2 for the Homepage billboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('home-billboard-sample-3', 'home-billboard', 'Sample Advertiser 3', 'images/ads/billboard-3.png', 'Placeholder creative 3 for the Homepage billboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('home-billboard-sample-4', 'home-billboard', 'Sample Advertiser 4', 'images/ads/billboard-4.png', 'Placeholder creative 4 for the Homepage billboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('home-billboard-sample-5', 'home-billboard', 'Sample Advertiser 5', 'images/ads/billboard-5.png', 'Placeholder creative 5 for the Homepage billboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('home-billboard-sample-6', 'home-billboard', 'Sample Advertiser 6', 'images/ads/billboard-6.png', 'Placeholder creative 6 for the Homepage billboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('directory-sidebar-sample-1', 'directory-sidebar', 'Sample Advertiser 1', 'images/ads/rectangle-1.png', 'Placeholder creative 1 for the Directory sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('directory-sidebar-sample-2', 'directory-sidebar', 'Sample Advertiser 2', 'images/ads/rectangle-2.png', 'Placeholder creative 2 for the Directory sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('directory-sidebar-sample-3', 'directory-sidebar', 'Sample Advertiser 3', 'images/ads/rectangle-3.png', 'Placeholder creative 3 for the Directory sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('directory-sidebar-sample-4', 'directory-sidebar', 'Sample Advertiser 4', 'images/ads/rectangle-4.png', 'Placeholder creative 4 for the Directory sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('directory-sidebar-sample-5', 'directory-sidebar', 'Sample Advertiser 5', 'images/ads/rectangle-5.png', 'Placeholder creative 5 for the Directory sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('directory-sidebar-sample-6', 'directory-sidebar', 'Sample Advertiser 6', 'images/ads/rectangle-6.png', 'Placeholder creative 6 for the Directory sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('directory-infeed-sample-1', 'directory-infeed', 'Sample Advertiser 1', 'images/ads/rectangle-1.png', 'Placeholder creative 1 for the Directory in-feed slot', '', 'none', true, current_date, current_date + 90, 1),
  ('directory-infeed-sample-2', 'directory-infeed', 'Sample Advertiser 2', 'images/ads/rectangle-2.png', 'Placeholder creative 2 for the Directory in-feed slot', '', 'none', true, current_date, current_date + 90, 1),
  ('directory-infeed-sample-3', 'directory-infeed', 'Sample Advertiser 3', 'images/ads/rectangle-3.png', 'Placeholder creative 3 for the Directory in-feed slot', '', 'none', true, current_date, current_date + 90, 1),
  ('directory-infeed-sample-4', 'directory-infeed', 'Sample Advertiser 4', 'images/ads/rectangle-4.png', 'Placeholder creative 4 for the Directory in-feed slot', '', 'none', true, current_date, current_date + 90, 1),
  ('directory-infeed-sample-5', 'directory-infeed', 'Sample Advertiser 5', 'images/ads/rectangle-5.png', 'Placeholder creative 5 for the Directory in-feed slot', '', 'none', true, current_date, current_date + 90, 1),
  ('directory-infeed-sample-6', 'directory-infeed', 'Sample Advertiser 6', 'images/ads/rectangle-6.png', 'Placeholder creative 6 for the Directory in-feed slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-leaderboard-sample-1', 'tenders-leaderboard', 'Sample Advertiser 1', 'images/ads/leaderboard-1.png', 'Placeholder creative 1 for the Tenders board leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-leaderboard-sample-2', 'tenders-leaderboard', 'Sample Advertiser 2', 'images/ads/leaderboard-2.png', 'Placeholder creative 2 for the Tenders board leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-leaderboard-sample-3', 'tenders-leaderboard', 'Sample Advertiser 3', 'images/ads/leaderboard-3.png', 'Placeholder creative 3 for the Tenders board leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-leaderboard-sample-4', 'tenders-leaderboard', 'Sample Advertiser 4', 'images/ads/leaderboard-4.png', 'Placeholder creative 4 for the Tenders board leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-leaderboard-sample-5', 'tenders-leaderboard', 'Sample Advertiser 5', 'images/ads/leaderboard-5.png', 'Placeholder creative 5 for the Tenders board leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-leaderboard-sample-6', 'tenders-leaderboard', 'Sample Advertiser 6', 'images/ads/leaderboard-6.png', 'Placeholder creative 6 for the Tenders board leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-infeed-sample-1', 'tenders-infeed', 'Sample Advertiser 1', 'images/ads/rectangle-1.png', 'Placeholder creative 1 for the Tenders in-feed slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-infeed-sample-2', 'tenders-infeed', 'Sample Advertiser 2', 'images/ads/rectangle-2.png', 'Placeholder creative 2 for the Tenders in-feed slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-infeed-sample-3', 'tenders-infeed', 'Sample Advertiser 3', 'images/ads/rectangle-3.png', 'Placeholder creative 3 for the Tenders in-feed slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-infeed-sample-4', 'tenders-infeed', 'Sample Advertiser 4', 'images/ads/rectangle-4.png', 'Placeholder creative 4 for the Tenders in-feed slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-infeed-sample-5', 'tenders-infeed', 'Sample Advertiser 5', 'images/ads/rectangle-5.png', 'Placeholder creative 5 for the Tenders in-feed slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-infeed-sample-6', 'tenders-infeed', 'Sample Advertiser 6', 'images/ads/rectangle-6.png', 'Placeholder creative 6 for the Tenders in-feed slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-sample-1', 'tenders-sidebar', 'Sample Advertiser 1', 'images/ads/rectangle-1.png', 'Placeholder creative 1 for the Tenders sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-sample-2', 'tenders-sidebar', 'Sample Advertiser 2', 'images/ads/rectangle-2.png', 'Placeholder creative 2 for the Tenders sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-sample-3', 'tenders-sidebar', 'Sample Advertiser 3', 'images/ads/rectangle-3.png', 'Placeholder creative 3 for the Tenders sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-sample-4', 'tenders-sidebar', 'Sample Advertiser 4', 'images/ads/rectangle-4.png', 'Placeholder creative 4 for the Tenders sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-sample-5', 'tenders-sidebar', 'Sample Advertiser 5', 'images/ads/rectangle-5.png', 'Placeholder creative 5 for the Tenders sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-sample-6', 'tenders-sidebar', 'Sample Advertiser 6', 'images/ads/rectangle-6.png', 'Placeholder creative 6 for the Tenders sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-leaderboard-sample-1', 'jobs-leaderboard', 'Sample Advertiser 1', 'images/ads/leaderboard-1.png', 'Placeholder creative 1 for the Jobs top leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-leaderboard-sample-2', 'jobs-leaderboard', 'Sample Advertiser 2', 'images/ads/leaderboard-2.png', 'Placeholder creative 2 for the Jobs top leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-leaderboard-sample-3', 'jobs-leaderboard', 'Sample Advertiser 3', 'images/ads/leaderboard-3.png', 'Placeholder creative 3 for the Jobs top leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-leaderboard-sample-4', 'jobs-leaderboard', 'Sample Advertiser 4', 'images/ads/leaderboard-4.png', 'Placeholder creative 4 for the Jobs top leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-leaderboard-sample-5', 'jobs-leaderboard', 'Sample Advertiser 5', 'images/ads/leaderboard-5.png', 'Placeholder creative 5 for the Jobs top leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-leaderboard-sample-6', 'jobs-leaderboard', 'Sample Advertiser 6', 'images/ads/leaderboard-6.png', 'Placeholder creative 6 for the Jobs top leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-sample-1', 'jobs-sidebar', 'Sample Advertiser 1', 'images/ads/rectangle-1.png', 'Placeholder creative 1 for the Jobs sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-sample-2', 'jobs-sidebar', 'Sample Advertiser 2', 'images/ads/rectangle-2.png', 'Placeholder creative 2 for the Jobs sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-sample-3', 'jobs-sidebar', 'Sample Advertiser 3', 'images/ads/rectangle-3.png', 'Placeholder creative 3 for the Jobs sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-sample-4', 'jobs-sidebar', 'Sample Advertiser 4', 'images/ads/rectangle-4.png', 'Placeholder creative 4 for the Jobs sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-sample-5', 'jobs-sidebar', 'Sample Advertiser 5', 'images/ads/rectangle-5.png', 'Placeholder creative 5 for the Jobs sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-sample-6', 'jobs-sidebar', 'Sample Advertiser 6', 'images/ads/rectangle-6.png', 'Placeholder creative 6 for the Jobs sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-sample-1', 'news-sidebar', 'Sample Advertiser 1', 'images/ads/rectangle-1.png', 'Placeholder creative 1 for the News sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-sample-2', 'news-sidebar', 'Sample Advertiser 2', 'images/ads/rectangle-2.png', 'Placeholder creative 2 for the News sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-sample-3', 'news-sidebar', 'Sample Advertiser 3', 'images/ads/rectangle-3.png', 'Placeholder creative 3 for the News sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-sample-4', 'news-sidebar', 'Sample Advertiser 4', 'images/ads/rectangle-4.png', 'Placeholder creative 4 for the News sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-sample-5', 'news-sidebar', 'Sample Advertiser 5', 'images/ads/rectangle-5.png', 'Placeholder creative 5 for the News sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-sample-6', 'news-sidebar', 'Sample Advertiser 6', 'images/ads/rectangle-6.png', 'Placeholder creative 6 for the News sidebar slot', '', 'none', true, current_date, current_date + 90, 1),
  ('footer-leaderboard-sample-1', 'footer-leaderboard', 'Sample Advertiser 1', 'images/ads/footer-1.png', 'Placeholder creative 1 for the Footer leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('footer-leaderboard-sample-2', 'footer-leaderboard', 'Sample Advertiser 2', 'images/ads/footer-2.png', 'Placeholder creative 2 for the Footer leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('footer-leaderboard-sample-3', 'footer-leaderboard', 'Sample Advertiser 3', 'images/ads/footer-3.png', 'Placeholder creative 3 for the Footer leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('footer-leaderboard-sample-4', 'footer-leaderboard', 'Sample Advertiser 4', 'images/ads/footer-4.png', 'Placeholder creative 4 for the Footer leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('footer-leaderboard-sample-5', 'footer-leaderboard', 'Sample Advertiser 5', 'images/ads/footer-5.png', 'Placeholder creative 5 for the Footer leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('footer-leaderboard-sample-6', 'footer-leaderboard', 'Sample Advertiser 6', 'images/ads/footer-6.png', 'Placeholder creative 6 for the Footer leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-2-sample-1', 'jobs-sidebar-2', 'Sample Advertiser 1', 'images/ads/rectangle-1.png', 'Placeholder creative 1 for the Jobs sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-2-sample-2', 'jobs-sidebar-2', 'Sample Advertiser 2', 'images/ads/rectangle-2.png', 'Placeholder creative 2 for the Jobs sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-2-sample-3', 'jobs-sidebar-2', 'Sample Advertiser 3', 'images/ads/rectangle-3.png', 'Placeholder creative 3 for the Jobs sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-2-sample-4', 'jobs-sidebar-2', 'Sample Advertiser 4', 'images/ads/rectangle-4.png', 'Placeholder creative 4 for the Jobs sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-2-sample-5', 'jobs-sidebar-2', 'Sample Advertiser 5', 'images/ads/rectangle-5.png', 'Placeholder creative 5 for the Jobs sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-2-sample-6', 'jobs-sidebar-2', 'Sample Advertiser 6', 'images/ads/rectangle-6.png', 'Placeholder creative 6 for the Jobs sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-3-sample-1', 'jobs-sidebar-3', 'Sample Advertiser 1', 'images/ads/rectangle-1.png', 'Placeholder creative 1 for the Jobs sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-3-sample-2', 'jobs-sidebar-3', 'Sample Advertiser 2', 'images/ads/rectangle-2.png', 'Placeholder creative 2 for the Jobs sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-3-sample-3', 'jobs-sidebar-3', 'Sample Advertiser 3', 'images/ads/rectangle-3.png', 'Placeholder creative 3 for the Jobs sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-3-sample-4', 'jobs-sidebar-3', 'Sample Advertiser 4', 'images/ads/rectangle-4.png', 'Placeholder creative 4 for the Jobs sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-3-sample-5', 'jobs-sidebar-3', 'Sample Advertiser 5', 'images/ads/rectangle-5.png', 'Placeholder creative 5 for the Jobs sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('jobs-sidebar-3-sample-6', 'jobs-sidebar-3', 'Sample Advertiser 6', 'images/ads/rectangle-6.png', 'Placeholder creative 6 for the Jobs sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-leaderboard-sample-1', 'news-leaderboard', 'Sample Advertiser 1', 'images/ads/leaderboard-1.png', 'Placeholder creative 1 for the News top leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-leaderboard-sample-2', 'news-leaderboard', 'Sample Advertiser 2', 'images/ads/leaderboard-2.png', 'Placeholder creative 2 for the News top leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-leaderboard-sample-3', 'news-leaderboard', 'Sample Advertiser 3', 'images/ads/leaderboard-3.png', 'Placeholder creative 3 for the News top leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-leaderboard-sample-4', 'news-leaderboard', 'Sample Advertiser 4', 'images/ads/leaderboard-4.png', 'Placeholder creative 4 for the News top leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-leaderboard-sample-5', 'news-leaderboard', 'Sample Advertiser 5', 'images/ads/leaderboard-5.png', 'Placeholder creative 5 for the News top leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-leaderboard-sample-6', 'news-leaderboard', 'Sample Advertiser 6', 'images/ads/leaderboard-6.png', 'Placeholder creative 6 for the News top leaderboard slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-2-sample-1', 'news-sidebar-2', 'Sample Advertiser 1', 'images/ads/rectangle-1.png', 'Placeholder creative 1 for the News sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-2-sample-2', 'news-sidebar-2', 'Sample Advertiser 2', 'images/ads/rectangle-2.png', 'Placeholder creative 2 for the News sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-2-sample-3', 'news-sidebar-2', 'Sample Advertiser 3', 'images/ads/rectangle-3.png', 'Placeholder creative 3 for the News sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-2-sample-4', 'news-sidebar-2', 'Sample Advertiser 4', 'images/ads/rectangle-4.png', 'Placeholder creative 4 for the News sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-2-sample-5', 'news-sidebar-2', 'Sample Advertiser 5', 'images/ads/rectangle-5.png', 'Placeholder creative 5 for the News sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-2-sample-6', 'news-sidebar-2', 'Sample Advertiser 6', 'images/ads/rectangle-6.png', 'Placeholder creative 6 for the News sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-3-sample-1', 'news-sidebar-3', 'Sample Advertiser 1', 'images/ads/rectangle-1.png', 'Placeholder creative 1 for the News sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-3-sample-2', 'news-sidebar-3', 'Sample Advertiser 2', 'images/ads/rectangle-2.png', 'Placeholder creative 2 for the News sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-3-sample-3', 'news-sidebar-3', 'Sample Advertiser 3', 'images/ads/rectangle-3.png', 'Placeholder creative 3 for the News sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-3-sample-4', 'news-sidebar-3', 'Sample Advertiser 4', 'images/ads/rectangle-4.png', 'Placeholder creative 4 for the News sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-3-sample-5', 'news-sidebar-3', 'Sample Advertiser 5', 'images/ads/rectangle-5.png', 'Placeholder creative 5 for the News sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('news-sidebar-3-sample-6', 'news-sidebar-3', 'Sample Advertiser 6', 'images/ads/rectangle-6.png', 'Placeholder creative 6 for the News sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-2-sample-1', 'tenders-sidebar-2', 'Sample Advertiser 1', 'images/ads/rectangle-1.png', 'Placeholder creative 1 for the Tenders sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-2-sample-2', 'tenders-sidebar-2', 'Sample Advertiser 2', 'images/ads/rectangle-2.png', 'Placeholder creative 2 for the Tenders sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-2-sample-3', 'tenders-sidebar-2', 'Sample Advertiser 3', 'images/ads/rectangle-3.png', 'Placeholder creative 3 for the Tenders sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-2-sample-4', 'tenders-sidebar-2', 'Sample Advertiser 4', 'images/ads/rectangle-4.png', 'Placeholder creative 4 for the Tenders sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-2-sample-5', 'tenders-sidebar-2', 'Sample Advertiser 5', 'images/ads/rectangle-5.png', 'Placeholder creative 5 for the Tenders sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-2-sample-6', 'tenders-sidebar-2', 'Sample Advertiser 6', 'images/ads/rectangle-6.png', 'Placeholder creative 6 for the Tenders sidebar, second slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-3-sample-1', 'tenders-sidebar-3', 'Sample Advertiser 1', 'images/ads/rectangle-1.png', 'Placeholder creative 1 for the Tenders sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-3-sample-2', 'tenders-sidebar-3', 'Sample Advertiser 2', 'images/ads/rectangle-2.png', 'Placeholder creative 2 for the Tenders sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-3-sample-3', 'tenders-sidebar-3', 'Sample Advertiser 3', 'images/ads/rectangle-3.png', 'Placeholder creative 3 for the Tenders sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-3-sample-4', 'tenders-sidebar-3', 'Sample Advertiser 4', 'images/ads/rectangle-4.png', 'Placeholder creative 4 for the Tenders sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-3-sample-5', 'tenders-sidebar-3', 'Sample Advertiser 5', 'images/ads/rectangle-5.png', 'Placeholder creative 5 for the Tenders sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1),
  ('tenders-sidebar-3-sample-6', 'tenders-sidebar-3', 'Sample Advertiser 6', 'images/ads/rectangle-6.png', 'Placeholder creative 6 for the Tenders sidebar, third slot', '', 'none', true, current_date, current_date + 90, 1)
on conflict (campaign_id) do update set
  slot = excluded.slot, advertiser = excluded.advertiser,
  image_url = excluded.image_url, alt = excluded.alt, link = excluded.link,
  link_type = excluded.link_type, active = excluded.active,
  starts_on = excluded.starts_on, ends_on = excluded.ends_on, weight = excluded.weight;

-- Check: every slot should show 6.
select slot, count(*) as campaigns
from ads where active and ends_on >= current_date
group by slot order by slot;
