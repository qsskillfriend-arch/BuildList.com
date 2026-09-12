from playwright.sync_api import sync_playwright
import json, sys, re

U = 'http://localhost:8899/'
results = []
def check(name, cond, detail=''):
    results.append((bool(cond), name, detail))

errs = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1400, 'height': 1000})
    pg.on('pageerror', lambda e: errs.append('PAGEERROR ' + str(e)))
    pg.on('console', lambda m: errs.append('CONSOLE ' + m.text)
          if m.type == 'error' and '403' not in m.text and 'fonts' not in m.text.lower() else None)

    # ═══ SHELL ═══
    pg.goto(U + 'index.html'); pg.wait_for_timeout(2500)
    check('Topbar: No.1 claim restored',
          "No.1 Construction Industry Platform" in pg.inner_text('.topbar-claim'))
    check('Topbar: Sharplink attribution kept',
          'Sharplink Ventures (U) Limited' in pg.inner_text('.owner-badge'))
    check('Data loaded', pg.evaluate('DATA_READY'))
    NF = pg.evaluate('DATA.firms.length')
    check('Hero stat matches dataset',
          pg.evaluate('document.getElementById("stat-firms").textContent').replace(',', '') == str(NF),
          pg.evaluate('document.getElementById("stat-firms").textContent') + ' vs ' + str(NF))
    check('Featured firms render',
          pg.evaluate('document.querySelectorAll("#featuredListings .listing-card").length') == 3)
    check('Price ticker renders',
          pg.evaluate('document.querySelectorAll("#priceTicker .price-item").length') > 0)
    check('Logo fallback to initials when none supplied',
          pg.evaluate('document.querySelectorAll("#featuredListings .listing-logo").length') == 3)
    check('Ads: one filled, rest available',
          pg.evaluate('document.querySelectorAll(".ad-filled").length') >= 1 and
          pg.evaluate('document.querySelectorAll(".ad-empty").length') >= 10)

    # ═══ ROUTING ═══
    for route, expect in [('#/directory', 'page-directory'), ('#/tenders', 'page-tenders'),
                          ('#/jobs', 'page-jobs'), ('#/news', 'page-news'),
                          ('#/advertise', 'page-advertise'), ('#/submit', 'page-submit'),
                          ('#/about', 'page-about')]:
        pg.goto(U + 'index.html' + route); pg.wait_for_timeout(700)
        vis = pg.evaluate('[...document.querySelectorAll("[id^=page-]:not(.hidden)")].map(e=>e.id)')
        check('Route ' + route, vis == [expect], str(vis))

    SLUG = pg.evaluate('DATA.firms[0].slug'); FNAME = pg.evaluate('DATA.firms[0].name')
    pg.goto(U + 'index.html#/firms/' + SLUG); pg.wait_for_timeout(1200)
    check('Route #/firms/:slug', FNAME in pg.inner_text('#profileContent h1'), SLUG)
    check('Profile sets page title', FNAME.split()[0] in pg.title())
    pg.goto(U + 'index.html#/firms/nope-not-real'); pg.wait_for_timeout(700)
    check('Bad slug shows recovery state',
          pg.evaluate('!!document.querySelector("#profileContent .empty-state")'))

    # ═══ SEARCH + FILTERS ═══
    pg.goto(U + 'index.html#/directory'); pg.wait_for_timeout(1400)
    check('Directory lists all firms',
          pg.evaluate('document.querySelectorAll("#dirListings .dir-listing-row").length') == NF)
    check('Facet counts computed (not hardcoded)',
          '0' in pg.evaluate('[...document.querySelectorAll(".filter-count")].map(e=>e.textContent).join(",")'))
    KLA = pg.evaluate('DATA.firms.filter(f=>f.district==="kampala").length')
    pg.evaluate('document.getElementById("f-districts-kampala").click()'); pg.wait_for_timeout(1200)
    check('Sidebar filter works',
          pg.evaluate('document.querySelectorAll("#dirListings .dir-listing-row").length') == KLA,
          str(KLA))
    check('Filter writes to URL', 'dist=kampala' in pg.evaluate('location.hash'))
    check('Active filter chip appears',
          pg.evaluate('document.querySelectorAll("#dirActiveFilters .chip").length') == 1)
    pg.evaluate('document.querySelector("#dirActiveFilters .chip button").click()'); pg.wait_for_timeout(1200)
    check('Chip removal restores results',
          pg.evaluate('document.querySelectorAll("#dirListings .dir-listing-row").length') == NF)

    TERM = pg.evaluate('DATA.firms[0].name.split(" ")[0].toLowerCase()')
    pg.goto(U + 'index.html#/directory?q=' + TERM); pg.wait_for_timeout(1500)
    check('Text search works',
          pg.evaluate('document.querySelectorAll("#dirListings .dir-listing-row").length') >= 1, TERM)
    pg.goto(U + 'index.html#/directory?q=zzzznope'); pg.wait_for_timeout(1200)
    check('Empty state offers to add the firm',
          'Suggest a listing' in pg.inner_text('#dirListings'))
    pg.goto(U + 'index.html#/directory?sort=name'); pg.wait_for_timeout(1800)
    first = pg.evaluate('document.querySelector("#dirListings .dir-row-name").textContent')
    expect = pg.evaluate('DATA.firms.map(f=>f.name).sort((a,b)=>a.localeCompare(b))[0]')
    check('Sort by name', first == expect, first + ' vs ' + expect)
    pg.goto(U + 'index.html#/directory'); pg.wait_for_timeout(1800)
    check('Relevance ranks complete listings first',
          pg.evaluate('completeness(filterFirms(DATA.firms,FILTERS)[0]) >= completeness(filterFirms(DATA.firms,FILTERS)[DATA.firms.length-1])'))
    check('Paid-placement disclosed',
          'Paid placement is always labelled' in pg.inner_text('#page-directory'))

    # ═══ VIEWS ═══
    pg.click('[data-view=grid]'); pg.wait_for_timeout(800)
    check('Grid view renders',
          pg.evaluate('document.querySelectorAll("#dirGrid .gcard").length') == NF)
    check('Grid hides list', pg.evaluate('document.getElementById("dirListings").offsetHeight') == 0)
    check('Grid in URL', 'view=grid' in pg.evaluate('location.hash'))
    pg.click('[data-view=map]'); pg.wait_for_timeout(9500)
    check('Map view: renders map or fallback',
          pg.evaluate('LEAFLET_STATE') == 'ready' or
          pg.evaluate('!!document.querySelector(".map-fallback")'),
          'leaflet=' + str(pg.evaluate('LEAFLET_STATE')))
    check('Map fallback lists results with directions',
          pg.evaluate('LEAFLET_STATE') == 'ready' or
          pg.evaluate('document.querySelectorAll("#dirMap a[href*=openstreetmap]").length') == NF)
    pg.click('[data-view=list]'); pg.wait_for_timeout(700)
    check('Back to list view',
          pg.evaluate('document.querySelectorAll("#dirListings .dir-listing-row").length') == NF)
    CAT = pg.evaluate('DATA.taxonomy.categories[0].slug')
    NCAT = pg.evaluate('DATA.firms.filter(f=>f.categories.includes(DATA.taxonomy.categories[0].slug)).length')
    pg.goto(U + 'index.html#/directory?view=grid&cat=' + CAT); pg.wait_for_timeout(1800)
    check('Deep link: view + filter together',
          pg.evaluate('document.querySelectorAll("#dirGrid .gcard").length') == NCAT and
          pg.evaluate('document.querySelector(".dir-tab.active").dataset.view') == 'grid', str(NCAT))

    # ═══ STAGE 6 ═══
    pg.goto(U + 'index.html#/news'); pg.wait_for_timeout(1800)
    check('Price index sparklines',
          pg.evaluate('document.querySelectorAll("#priceIndex .spark-wrap").length') == 11)
    check('Price index shows % change',
          '%' in pg.inner_text('#priceIndex .spark-delta'))
    check('Price collection date shown',
          pg.evaluate('document.querySelector("[data-prices-updated]").textContent') != '—')

    pg.goto(U + 'index.html#/tenders'); pg.wait_for_timeout(1500)
    check('Tender alerts form renders',
          pg.evaluate('document.querySelectorAll("#alertForm .alert-cats label").length') >= 3)
    check('Alerts form is Netlify-wired',
          pg.evaluate('!!document.querySelector("form[name=tender-alerts][data-netlify]")'))
    check('Closed tenders auto-hidden',
          pg.evaluate('document.querySelectorAll("#tendersFull .tender-card-full").length') ==
          pg.evaluate('openTenders().length'))
    pg.select_option('#tenderStatus', 'urgent'); pg.wait_for_timeout(800)
    check('Tender filter works',
          pg.evaluate('document.querySelectorAll("#tendersFull .tender-card-full").length') <=
          pg.evaluate('openTenders().length'))

    pg.goto(U + 'index.html#/jobs'); pg.wait_for_timeout(1400)
    pg.select_option('#jobLevel', 'entry'); pg.wait_for_timeout(600)
    check('Job level filter',
          pg.evaluate('document.querySelectorAll("#jobsFull .job-card-full").length') == 1)
    pg.click('button[onclick="resetJobFilter()"]') if pg.query_selector('button[onclick="resetJobFilter()"]') else None
    pg.wait_for_timeout(400)

    pg.goto(U + 'index.html#/directory'); pg.wait_for_timeout(1400)
    pg.select_option('#rfqCat', CAT); pg.wait_for_timeout(600)
    check('RFQ responds to category choice',
          pg.evaluate('!!document.querySelector(".rfq-suppliers")'))
    check('RFQ only offers verified suppliers',
          pg.evaluate('''(() => { const v = document.getElementById("rfqMatched").value;
            if (!v) return true;
            return v.split(",").every(s => (DATA.firms.find(f=>f.slug===s)||{}).verified === true); })()'''))

    # ═══ FORMS ═══
    pg.goto(U + 'index.html#/submit'); pg.wait_for_timeout(1200)
    check('Listing form is Netlify-wired',
          pg.evaluate('!!document.querySelector("form[name=listing-submission][data-netlify]")'))
    check('Listing form fields all named',
          pg.evaluate('[...document.querySelectorAll("form[name=listing-submission] input,form[name=listing-submission] select,form[name=listing-submission] textarea")].every(e=>e.name)'))
    pg.goto(U + 'index.html#/about'); pg.wait_for_timeout(1000)
    check('Contact form wired',
          pg.evaluate('!!document.querySelector("form[name=contact][data-netlify]")'))
    check('Ownership block on About',
          'Sharplink Ventures (U) Limited' in pg.inner_text('#page-about'))
    check('Regulator disclosure present',
          'not affiliated with' in pg.inner_text('#page-about').lower())

    # ═══ ACCESSIBILITY / MOBILE ═══
    check('Skip link exists', pg.evaluate('!!document.querySelector(".skip-link")'))
    check('Main landmark', pg.evaluate('!!document.querySelector("main#main")'))
    check('No emoji left as icons',
          pg.evaluate(r'''!/[\u{1F300}-\u{1FAFF}]/u.test(document.body.innerText)'''))

    mob = b.new_page(viewport={'width': 390, 'height': 844})
    mob.goto(U + 'index.html#/directory'); mob.wait_for_timeout(1800)
    check('Mobile: no horizontal overflow',
          mob.evaluate('document.documentElement.scrollWidth') == 390,
          str(mob.evaluate('document.documentElement.scrollWidth')))
    mob.goto(U + 'index.html'); mob.wait_for_timeout(1200)
    mob.click('.nav-toggle'); mob.wait_for_timeout(500)
    check('Mobile nav opens',
          mob.evaluate('document.getElementById("mobileNav").classList.contains("open")'))
    check('Mobile: No.1 claim visible',
          mob.evaluate('document.querySelector(".topbar-claim").offsetHeight') > 0)

    # ═══ STAGE 5 STATIC PAGES ═══
    pg.goto(U + 'firms/' + SLUG + '/'); pg.wait_for_timeout(800)
    check('Static firm page serves', FNAME.split()[0] in pg.title(), SLUG)
    check('Static page has canonical',
          '/firms/' + SLUG + '/' in pg.evaluate('document.querySelector("link[rel=canonical]").href'))
    ld = pg.evaluate('JSON.parse(document.querySelector("script[type=\'application/ld+json\']").textContent)')
    check('LocalBusiness structured data', ld.get('@type') == 'LocalBusiness')
    check('aggregateRating only when reviews exist',
          ('aggregateRating' in ld) == (ld.get('aggregateRating', {}).get('reviewCount', 0) > 0))
    check('Static page readable without JS',
          len(pg.inner_text('main')) > 200)
    pg.goto(U + 'browse/quantity-surveying-kampala/'); pg.wait_for_timeout(700)
    check('Category x district page serves',
          'Quantity Surveying in Kampala' in pg.title(), pg.title())
    pg.goto(U + 'browse/'); pg.wait_for_timeout(600)
    check('Directory index page serves', 'directory' in pg.title().lower())
    check('Browse index links to category pages',
          pg.evaluate('document.querySelectorAll(".links a").length') > 10)

    # ═══ ADMIN ═══
    ad = b.new_page(viewport={'width': 1440, 'height': 900})
    ad.on('dialog', lambda d: d.accept())
    ad.goto(U + 'admin.html'); ad.wait_for_timeout(700)
    ad.fill('#pw', 'buildlist'); ad.click('#gate button'); ad.wait_for_timeout(1800)
    check('Admin unlocks', ad.evaluate('document.getElementById("app").classList.contains("on")'))
    check('Admin loads all 7 data files',
          ad.evaluate('Object.keys(DB).length') >= 7, str(ad.evaluate('Object.keys(DB)')))
    check('Admin board shows worklist',
          ad.evaluate('document.querySelectorAll(".task").length') >= 3)
    for sec in ['firms', 'tenders', 'jobs', 'articles', 'prices', 'ads']:
        ad.click('[data-go=' + sec + ']'); ad.wait_for_timeout(700)
        n = ad.evaluate('document.querySelectorAll("tbody tr").length')
        check('Admin ' + sec + ' table populated', n > 0, 'got ' + str(n))
    ad.click('[data-go=checks]'); ad.wait_for_timeout(500)
    check('Admin integrity checks run',
          ad.evaluate('document.querySelectorAll(".issue").length') > 0)
    ad.click('[data-go=firms]'); ad.wait_for_timeout(400)
    ad.click('.toolbar button.btn-p'); ad.wait_for_timeout(700)
    N0 = ad.evaluate('DB.firms.length')
    ad.fill('#e_name', 'Test Hardware Ltd'); ad.fill('#e_phone', '+256772000111')
    ad.evaluate('document.querySelector("input[name=e_cats]").checked = true')
    ad.click('.drawer-foot .btn-p'); ad.wait_for_timeout(900)
    check('Admin can add a firm', ad.evaluate('DB.firms.length') == N0 + 1)
    check('Admin auto-slugs', ad.evaluate('DB.firms[DB.firms.length-1].slug') == 'test-hardware-ltd')
    check('Admin marks file dirty', 'firms' in ad.evaluate('[...DIRTY]'))
    ad.click('.toolbar button.btn-p'); ad.wait_for_timeout(600)
    ad.click('.drawer-foot .btn-p'); ad.wait_for_timeout(400)
    check('Admin validation blocks bad save', ad.evaluate('DB.firms.length') == N0 + 1)

    b.close()

# ═══ REPORT ═══
passed = sum(1 for ok, _, _ in results if ok)
print('\n' + '=' * 66)
for ok, name, detail in results:
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('   [' + detail + ']') if detail and not ok else ''))
print('=' * 66)
print('%d/%d passed' % (passed, len(results)))
print('JS errors:', errs if errs else 'none')
sys.exit(0 if passed == len(results) and not errs else 1)
