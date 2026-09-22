-- ═══════════════════════════════════════════════════════════════
-- REMOVE SAMPLE CONTENT
-- Run this when you are ready to go live, or any time after.
--
-- The public site already hides everything below (it never shows a
-- sample advert or a sample monthly slot to a visitor), so this is
-- tidiness rather than urgency: it keeps your portal's Advertising
-- page showing only real campaigns.
-- ═══════════════════════════════════════════════════════════════

delete from ads where campaign_id like '%-sample-%';
delete from spotlight where name ilike 'sample %';

-- Check: both should be 0
select
  (select count(*) from ads where campaign_id like '%-sample-%') as sample_ads_left,
  (select count(*) from spotlight where name ilike 'sample %')   as sample_slots_left;
