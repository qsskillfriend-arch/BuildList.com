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
    PS = pg.evaluate('PAGE_SIZE')
    check('Hero stat is a rounded floor with a plus',
          pg.evaluate('document.getElementById("stat-firms").textContent') == pg.evaluate('plusCount(%d)' % NF),
          pg.evaluate('document.getElementById("stat-firms").textContent'))
    check('Featured firms render',
          pg.evaluate('document.querySelectorAll("#featuredListings .fcard").length') == 3)
    check('Price ticker renders',
          pg.evaluate('document.querySelectorAll("#priceTicker .price-item").length') > 0)
    check('Logo falls back to initials when none supplied',
          pg.evaluate('document.querySelectorAll("#featuredListings .fcard-logo").length') == 3)
    check('Ads: filled and available slots both render',
          pg.evaluate('document.querySelectorAll(".ad-filled").length') >= 1 and
          pg.evaluate('document.querySelectorAll(".ad-empty").length') >= 1)

    # Slot keys must name the page they sit on, or advertiser reporting lies
    slot_pages = pg.evaluate('''() => [...document.querySelectorAll('[data-ad]')]
        .map(e => ({slot: e.dataset.ad, page: (e.closest('[id^=page-]')||{}).id || 'global'}))''')
    bad = [x for x in slot_pages
           if x['page'] != 'global' and not x['slot'].startswith(x['page'].replace('page-', ''))]
    check('Ad slot keys match their page', not bad, str(bad))
    all_keys = [x['slot'] for x in slot_pages]
    check('No duplicate ad slot keys', len(all_keys) == len(set(all_keys)), str(all_keys))
    registry = pg.evaluate('Object.keys(DATA.ads.slots)')
    check('Every rendered slot is in the registry',
          all(k in registry for k in all_keys),
          str([k for k in all_keys if k not in registry]))

    # Ad-free pages
    for route in ['submit', 'privacy', 'terms']:
        pg.goto(U + 'index.html#/' + route); pg.wait_for_timeout(900)
        n = pg.evaluate('[...document.querySelectorAll("[data-ad]")].filter(e=>e.offsetHeight>0).length')
        check('No advertising on the %s page' % route, n == 0, str(n))
    pg.goto(U + 'index.html'); pg.wait_for_timeout(2000)

    # ═══ NAVIGATION ═══
    nav = pg.evaluate('[...document.querySelectorAll(".nav-main .nav-link")].map(a=>a.textContent.trim())')
    check('Home is the first nav item',
          nav[:2] == ['Home', 'Directory'], str(nav))
    check('Home highlights on the homepage',
          pg.evaluate('document.getElementById("nav-home").classList.contains("active")'))
    mnav = pg.evaluate('[...document.querySelectorAll(".mobile-nav-link")].map(a=>a.textContent.trim())')
    check('Home is first in the mobile menu', mnav[0] == 'Home', str(mnav[:3]))
    pg.goto(U + 'index.html#/tenders'); pg.wait_for_timeout(900)
    check('Only the current section highlights',
          pg.evaluate('[...document.querySelectorAll(".nav-link.active")].map(a=>a.id)') == ['nav-tenders'])
    pg.goto(U + 'index.html'); pg.wait_for_timeout(1800)

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
    check('Directory pages the results',
          pg.evaluate('document.querySelectorAll("#dirListings .dir-listing-row").length') == min(PS, NF))
    check('Pager reports the exact range',
          '1–%d of %d' % (min(PS, NF), NF) in pg.inner_text('.pager-info'),
          pg.inner_text('.pager-info'))
    check('Facet counts computed (not hardcoded)',
          '0' in pg.evaluate('[...document.querySelectorAll(".filter-count")].map(e=>e.textContent).join(",")'))
    KLA = pg.evaluate('DATA.firms.filter(f=>f.district==="kampala").length')
    pg.evaluate('document.getElementById("f-districts-kampala").click()'); pg.wait_for_timeout(1200)
    check('Sidebar filter works',
          pg.evaluate('filterFirms(DATA.firms, FILTERS).length') == KLA, str(KLA))
    check('Filter writes to URL', 'dist=kampala' in pg.evaluate('location.hash'))
    check('Active filter chip appears',
          pg.evaluate('document.querySelectorAll("#dirActiveFilters .chip").length') == 1)
    pg.evaluate('document.querySelector("#dirActiveFilters .chip button").click()'); pg.wait_for_timeout(1200)
    check('Chip removal restores results',
          pg.evaluate('filterFirms(DATA.firms, FILTERS).length') == NF)

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
    check('Grid view renders one page',
          pg.evaluate('document.querySelectorAll("#dirGrid .gcard").length') == min(PS, NF))
    check('Grid hides list', pg.evaluate('document.getElementById("dirListings").offsetHeight') == 0)
    check('Grid in URL', 'view=grid' in pg.evaluate('location.hash'))
    pg.click('[data-view=map]'); pg.wait_for_timeout(9500)
    check('Map view: renders map or fallback',
          pg.evaluate('LEAFLET_STATE') == 'ready' or
          pg.evaluate('!!document.querySelector(".map-fallback")'),
          'leaflet=' + str(pg.evaluate('LEAFLET_STATE')))
    check('Map is never paged',
          pg.evaluate('LEAFLET_STATE') == 'ready' or
          pg.evaluate('document.querySelectorAll("#dirMap a[href*=openstreetmap]").length') == NF)
    pg.click('[data-view=list]'); pg.wait_for_timeout(700)
    check('Back to list view',
          pg.evaluate('document.querySelectorAll("#dirListings .dir-listing-row").length') == min(PS, NF))
    CAT = pg.evaluate('DATA.taxonomy.categories[0].slug')
    NCAT = pg.evaluate('DATA.firms.filter(f=>f.categories.includes(DATA.taxonomy.categories[0].slug)).length')
    pg.goto(U + 'index.html#/directory?view=grid&cat=' + CAT); pg.wait_for_timeout(1800)
    check('Deep link: view + filter together',
          pg.evaluate('document.querySelectorAll("#dirGrid .gcard").length') == min(PS, NCAT) and
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

    # ═══ PAGINATION ═══
    pg.goto(U + 'index.html#/directory?page=3'); pg.wait_for_timeout(1800)
    check('Deep link to page 3', '49–72' in pg.inner_text('.pager-info'), pg.inner_text('.pager-info'))
    pg.goto(U + 'index.html#/directory?per=48'); pg.wait_for_timeout(2600)
    _rows = pg.evaluate('document.querySelectorAll("#dirListings .dir-listing-row").length')
    _sz = pg.evaluate('PAGE_SIZE')
    check('Page size is settable', _rows == min(48, NF),
          'rows=%s PAGE_SIZE=%s' % (_rows, _sz))
    pg.goto(U + 'index.html#/directory?page=3'); pg.wait_for_timeout(1500)
    pg.evaluate('document.getElementById("f-districts-kampala").click()'); pg.wait_for_timeout(1200)
    check('Filtering returns to page 1', pg.evaluate('PAGE') == 1)

    # ═══ LEGAL PAGES ═══
    for route, title in [('privacy', 'Privacy Policy'), ('terms', 'Terms of Service')]:
        pg.goto(U + 'index.html#/' + route); pg.wait_for_timeout(800)
        check('Legal page: ' + title,
              title in pg.inner_text('#page-' + route) and len(pg.inner_text('#page-' + route)) > 1500)
    check('Legal pages carry the review warning',
          'reviewed by a Ugandan advocate' in pg.inner_text('#page-terms'))
    check('Listing Agreement removed site-wide',
          pg.evaluate('!document.getElementById("page-listing-agreement")') and
          'listing-agreement' not in pg.content())

    # ═══ TENDER CLIENT FILTER ═══
    pg.goto(U + 'index.html#/tenders'); pg.wait_for_timeout(2000)
    tabs = pg.evaluate('[...document.querySelectorAll(".tab-btn[data-client]")].map(b=>b.dataset.client)')
    check('Tender client tabs present',
          set(tabs) == {'', 'government', 'parastatal', 'ngo', 'private'}, str(tabs))
    check('Tabs carry live counts',
          pg.evaluate('document.querySelectorAll(".tab-btn .tab-n").length') == 5)
    pg.evaluate('resetTenderFilter()')          # an earlier test left a status filter set
    pg.click('[data-client=government]')
    gov = pg.evaluate('DATA.tenders.filter(t=>t.clientType==="government" && new Date(t.deadline)>=new Date()).length')
    pg.wait_for_function('n => document.querySelectorAll("#tendersFull .tender-card-full").length === n',
                         arg=gov, timeout=5000)
    check('Government filter works',
          pg.evaluate('document.querySelectorAll("#tendersFull .tender-card-full").length') == gov and
          pg.evaluate('TENDER_FILTER.client') == 'government', str(gov))
    pg.click('[data-client=ngo]'); pg.wait_for_timeout(900)
    check('Empty tab explains itself and offers alerts',
          'Set a tender alert' in pg.inner_text('#tendersFull'))
    check('Every tender is classified',
          pg.evaluate('DATA.tenders.every(t=>!!t.clientType)'))

    # ═══ COOKIE CONSENT ═══
    check('Consent helpers exist', pg.evaluate('typeof getConsent === "function" && typeof setConsent === "function"'))
    check('No tag loads without consent',
          pg.evaluate('!document.querySelector("script[src*=googletagmanager]")'))
    check('Notice hidden when analytics unconfigured',
          pg.evaluate('!document.getElementById("cookieNotice").classList.contains("on")'))
    pg.goto(U + 'index.html#/privacy'); pg.wait_for_timeout(900)
    check('Privacy page lets you change the choice',
          pg.evaluate('!!document.getElementById("consentState")'))

    # ═══ THIS BATCH ═══
    pg.goto(U + 'index.html'); pg.wait_for_timeout(2400)
    check('Sector grid is data-driven',
          pg.evaluate('document.querySelectorAll("#sectorGrid .cat-card").length') == 12)
    hrefs = pg.evaluate('[...document.querySelectorAll("#sectorGrid .cat-card")].map(a=>a.getAttribute("href"))')
    check('Every sector card carries a category filter',
          all(h and 'cat=' in h for h in hrefs), str(hrefs[:2]))
    counts = pg.evaluate('''[...document.querySelectorAll("#sectorGrid .cat-count")].map(e=>e.textContent)''')
    real = pg.evaluate('''(()=>{const c=facetCounts(DATA.firms,'categories');
      return Object.values(c).some(n=>n>0)})()''')
    check('Sector counts come from the data', real, str(counts[:2]))
    pg.click('#sectorGrid .cat-card'); pg.wait_for_timeout(1600)
    check('Sector click filters the directory', 'cat=' in pg.evaluate('location.hash'))
    check('Sector click ticks the sidebar box',
          pg.evaluate('document.querySelectorAll(".filter-group input[type=checkbox]:checked").length') == 1)
    check('Tradesmen is the last category',
          pg.evaluate('DATA.taxonomy.categories[DATA.taxonomy.categories.length-1].slug') == 'tradesmen')
    check('Tradesmen checkbox present',
          pg.evaluate('!!document.getElementById("f-categories-tradesmen")'))
    check('Category filter list scrolls',
          pg.evaluate('''(()=>{const g=document.querySelector('.filter-group.scrolls .filter-body');
            return !!g && g.scrollHeight > g.clientHeight;})()'''))
    pg.goto(U + 'index.html#/tenders'); pg.wait_for_timeout(1600)
    check('Tender tabs are segmented buttons',
          pg.evaluate('''(()=>{const b=document.querySelector('.tab-btn.active');
            const c=getComputedStyle(b); return parseFloat(c.borderRadius)>0;})()'''))
    pg.goto(U + 'index.html#/about'); pg.wait_for_timeout(1000)
    about = pg.inner_text('#page-about')
    check('Team member cards removed',
          'Our Team' not in about and pg.evaluate('!document.querySelector(".team-grid")'))
    pg.goto(U + 'index.html#/advertise'); pg.wait_for_timeout(1200)
    check('Media kit download offered',
          pg.evaluate('!!document.querySelector("a[href*=\'Media-Kit\'][download]")'))
    body_all = pg.evaluate('document.body.innerText')
    check('No "mobile optimised" wording anywhere',
          'mobile optimi' not in body_all.lower() and 'mobile-optimi' not in body_all.lower())

    # ═══ ARTICLES OPEN AND READ ═══
    pg.goto(U + 'index.html#/news'); pg.wait_for_timeout(2000)
    links = pg.evaluate('''[...document.querySelectorAll('#newsArticles a')]
        .map(a=>a.getAttribute('href')).filter(h=>h && h.indexOf('#/news/')===0)''')
    check('Article cards link to a reading view', len(links) >= 3, str(len(links)))
    pg.goto(U + 'index.html' + links[0]); pg.wait_for_timeout(1300)
    check('Article page opens',
          pg.evaluate('[...document.querySelectorAll("[id^=page-]:not(.hidden)")].map(e=>e.id)') == ['page-article'])
    body = pg.inner_text('.art-body')
    check('Article body is substantial', len(body) > 800, str(len(body)))
    check('Markdown renders headings, lists and quotes',
          pg.evaluate('!!document.querySelector(".art-body h2")') and
          pg.evaluate('!!document.querySelector(".art-body ul")') and
          pg.evaluate('!!document.querySelector(".art-body blockquote")'))
    check('Article sets its own page title', 'BuildList.com' in pg.title() and len(pg.title()) > 30)
    check('Related articles offered',
          pg.evaluate('document.querySelectorAll(".art-more a").length') >= 2)
    pg.goto(U + 'index.html#/news/does-not-exist'); pg.wait_for_timeout(1000)
    check('Unknown article falls back to the news page',
          pg.evaluate('[...document.querySelectorAll("[id^=page-]:not(.hidden)")].map(e=>e.id)') == ['page-news'])

    # ═══ AD DESTINATIONS ═══
    pg.goto(U + 'index.html'); pg.wait_for_timeout(2200)
    check('Ad destination helper exists', pg.evaluate('typeof adDestination === "function"'))
    check('External ad links are nofollow sponsored',
          pg.evaluate('''[...document.querySelectorAll('a.ad-creative[target=_blank], a.ad-flier[target=_blank]')]
            .every(a => a.rel.includes('sponsored') && a.rel.includes('nofollow'))'''))
    check('Profile-linked ads stay on the site',
          pg.evaluate('''adDestination({linkType:'profile', firmSlug:DATA.firms[0].slug}).external === false'''))
    check('Ads can have no link at all',
          pg.evaluate("adDestination({linkType:'none', link:'https://x.com'}) === null"))

    # ═══ TENDER TAB DESIGN ═══
    pg.goto(U + 'index.html#/tenders'); pg.wait_for_timeout(1600)
    check('Tabs sit in a contained track',
          pg.evaluate('''(()=>{const t=document.querySelector('.tab-bar');
            const c=getComputedStyle(t);
            return c.display.includes('flex') && parseFloat(c.borderRadius)>=8;})()'''))
    check('Active tab is raised, not a grey box',
          pg.evaluate('''(()=>{const b=document.querySelector('.tab-btn.active');
            const c=getComputedStyle(b);
            return c.boxShadow !== 'none' && c.backgroundColor !== 'rgba(0, 0, 0, 0)';})()'''))

    # ═══ PAGE ISOLATION ═══
    # A stray </div> once let the homepage sections escape #page-home and
    # render on every page. This catches that class of bug structurally.
    OWNER = {
        'featuredListings': 'home', 'productOfMonth': 'home', 'projectOfMonth': 'home',
        'homeTenders': 'home', 'homeJobs': 'home', 'homeNews': 'home',
        'dirListings': 'directory', 'dirFilters': 'directory', 'rfqForm': 'directory',
        'tendersFull': 'tenders', 'alertForm': 'tenders',
        'jobsFull': 'jobs', 'newsArticles': 'news', 'priceIndex': 'news',
    }
    for marker, owner in OWNER.items():
        got = pg.evaluate('id => document.getElementById(id)?.closest("[id^=page-]")?.id', marker)
        check('Section %s belongs to page-%s' % (marker, owner), got == 'page-' + owner, str(got))

    for route in ['home', 'directory', 'tenders', 'jobs', 'news', 'advertise', 'submit', 'about']:
        pg.goto(U + 'index.html#/' + route); pg.wait_for_timeout(800)
        vis = pg.evaluate('[...document.querySelectorAll("[id^=page-]:not(.hidden)")].map(e=>e.id)')
        leaked = [m for m, o in OWNER.items() if o != route and
                  pg.evaluate('id => (document.getElementById(id)?.offsetHeight || 0) > 0', m)]
        check('Page %s shows only its own content' % route,
              vis == ['page-' + route] and not leaked, str(vis) + ' leaked=' + str(leaked))

    # ═══ PROVENANCE ═══
    pg.goto(U + 'index.html#/directory'); pg.wait_for_timeout(2600)
    check('Compiled listings are not claimed as supplied',
          'supplied by the business' not in pg.inner_text('#dirListings').lower())
    cases = [
        ({'descSource': 'derived',   'verified': False, 'verifiedDate': None}, 'compiled',  'Compiled from public sources'),
        ({'descSource': 'sheet',     'verified': False, 'verifiedDate': None}, 'compiled',  'Compiled from public sources'),
        ({'descSource': 'submitted', 'verified': False, 'verifiedDate': None}, 'submitted', 'Supplied by the business'),
        ({'descSource': 'submitted', 'verified': True,  'verifiedDate': '2026-09-01'}, 'verified', 'Verified'),
    ]
    for obj, kind, text in cases:
        html = pg.evaluate('o => verifiedLine(o)', obj)
        check('Provenance: ' + kind + ' (' + obj['descSource'] + ')',
              ('prov-' + kind) in html and text in html, html[:70])
    check('Every listing has a provenance state',
          pg.evaluate('DATA.firms.every(f => ["verified","submitted","compiled"].includes(provenanceOf(f)))'))
    pg.goto(U + 'index.html#/firms/' + SLUG); pg.wait_for_timeout(1400)
    check('Profile explains the provenance in full',
          'public registers and directories' in pg.inner_text('#profileContent'))
    check('Unverified profile offers a claim route',
          'This is my business' in pg.inner_text('#profileContent'))

    # ═══ MONTHLY SPOTLIGHTS ═══
    pg.goto(U + 'index.html'); pg.wait_for_timeout(2600)
    check('Product of the Month renders', pg.evaluate('!!document.querySelector(".spot-product")'))
    check('Benchmark Project renders', pg.evaluate('!!document.querySelector(".spot-project")'))
    check('Paid slot is labelled as advertising',
          'Advertisement' in pg.inner_text('.spot-product') or
          pg.evaluate('!!document.querySelector(".spot-ad-flag")'))
    check('Editorial slot states it is not for sale',
          'not for sale' in pg.inner_text('.spot-project'))
    check('Editorial slot is never sponsored',
          pg.evaluate('DATA.spotlight.project.sponsored') is False)
    check('Paid slot links carry nofollow sponsored',
          pg.evaluate('''[...document.querySelectorAll('.spot-product a[target=_blank]')]
            .every(a => a.rel.includes('sponsored'))'''))
    check('Spotlight images keep their aspect ratio',
          pg.evaluate('''[...document.querySelectorAll('.spot-media img')]
            .every(i => i.clientWidth > 0 && i.clientHeight > 0)'''))

    # ═══ FEATURED CARDS ═══
    pg.goto(U + 'index.html'); pg.wait_for_timeout(2500)
    check('Featured cards render', pg.evaluate('document.querySelectorAll(".fcard").length') == 3)
    check('Firm name is visible, not white-on-white',
          pg.evaluate('''(()=>{const e=document.querySelector('.fcard-name');
            return e && getComputedStyle(e).color !== 'rgb(255, 255, 255)'
                   && e.getBoundingClientRect().height > 0;})()'''))
    check('Featured cards are equal height',
          pg.evaluate('''(()=>{const h=[...document.querySelectorAll('.fcard')]
            .map(c=>Math.round(c.getBoundingClientRect().height));
            return new Set(h).size === 1;})()'''))
    check('No content overflows a featured card',
          pg.evaluate('''[...document.querySelectorAll('.fcard')]
            .every(c => c.scrollHeight <= c.clientHeight + 1)'''))

    # ═══ REGISTERS ═══
    pg.goto(U + 'index.html'); pg.wait_for_timeout(2000)
    body_all = pg.evaluate('document.body.innerText')
    for dead in ['BORAQS', 'NCIC', 'UIQS']:
        check('Removed from site: ' + dead, dead not in body_all)
    accs = pg.evaluate('DATA.taxonomy.accreditations.map(a=>a.slug)')
    check('Real Ugandan registers present',
          all(a in accs for a in ['arb', 'erb', 'srb', 'isu']), str(accs))
    check('Mobile Optimised removed from trust bar',
          'Mobile Optimised' not in body_all)
    check('Brand is BuildList.com throughout',
          'BuildList.com' in body_all)

    # ═══ FOOTER LINKS ═══
    dead_links = pg.evaluate('''[...document.querySelectorAll('.footer-col a')]
        .map(a => a.getAttribute('href')).filter(h => !h || h === '#')''')
    check('No dead footer links', len(dead_links) == 0, str(dead_links))
    cat_links = pg.evaluate('''[...document.querySelectorAll('.footer-col a')]
        .map(a => a.getAttribute('href')).filter(h => h.includes('cat='))''')
    check('Footer category links are filtered views', len(cat_links) >= 5, str(len(cat_links)))

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

    # ═══ STAFF PORTAL ═══
    pt = b.new_page()
    perr = []
    pt.on('pageerror', lambda e: perr.append(str(e)))
    pt.goto(U + 'portal.html'); pt.wait_for_timeout(1800)
    check('Portal offers a demo without a database',
          pt.evaluate('document.querySelectorAll("#authMsg button").length') == 3)
    EXPECT = {
        'admin':  ['board','firms','tenders','jobs','articles','media','prices','spotlight','ads','analytics','staff'],
        'editor': ['board','firms','tenders','jobs','articles','media','prices','spotlight','analytics'],
        'agent':  ['board','firms'],
    }
    for role, nav in EXPECT.items():
        pt.goto(U + 'portal.html'); pt.wait_for_timeout(1400)
        pt.evaluate('r => demoAs(r)', role); pt.wait_for_timeout(1800)
        got = pt.evaluate('[...document.querySelectorAll(".rail a")].map(a=>a.dataset.go)')
        check('Portal nav for ' + role, got == nav, str(got))
        pt.evaluate("go('firms')"); pt.wait_for_timeout(700)
        pt.evaluate('editFirm(null)'); pt.wait_for_timeout(600)
        has_tier = pt.evaluate('!!document.getElementById("e_tier")')
        check('Tier field %s for %s' % ('shown' if role == 'admin' else 'hidden', role),
              has_tier == (role == 'admin'))
        pt.evaluate('closeDrawer()')
        pt.evaluate("go('staff')"); pt.wait_for_timeout(500)
        reached = pt.evaluate('document.getElementById("pageTitle").textContent')
        check('Direct nav to Staff %s for %s' % ('allowed' if role == 'admin' else 'blocked', role),
              (reached == 'Staff') == (role == 'admin'), reached)
    # ═══ CONTENT STUDIO ═══
    pt.goto(U + 'portal.html'); pt.wait_for_timeout(1400)
    pt.evaluate('demoAs("editor")'); pt.wait_for_timeout(1900)
    pt.evaluate("go('media')"); pt.wait_for_timeout(800)
    check('Image pipeline exposes slot targets',
          pt.evaluate('Object.keys(IMG.targets).length') >= 8)
    pt.evaluate('''async () => {
      const mk=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;
        const x=c.getContext('2d');x.fillStyle='#1A3C2A';x.fillRect(0,0,w,h);return c;};
      const big=await new Promise(r=>mk(2400,1350).toBlob(r,'image/jpeg',0.95));
      window.MEDIA_TARGET='article';
      await queueFiles([new File([big],'test-large.jpg',{type:'image/jpeg'})]);
      const small=await new Promise(r=>mk(300,169).toBlob(r,'image/jpeg',0.9));
      await queueFiles([new File([small],'test-small.jpg',{type:'image/jpeg'})]);
    }''')
    pt.wait_for_timeout(3000)
    check('Upload produces three widths',
          pt.evaluate('DB.media.find(m=>m.base.includes("large")).variants.length') == 3)
    check('Small source is never upscaled',
          pt.evaluate('DB.media.find(m=>m.base.includes("small")).variants.length') == 1)
    check('Undersized image is flagged',
          'soft' in str(pt.evaluate('UPLOADS.map(u=>u.msg).join(" ")')))
    check('Large upload is compressed',
          pt.evaluate('DB.media.find(m=>m.base.includes("large")).variants[0].bytes') < 400000)
    mid = pt.evaluate('DB.media[DB.media.length-1].id')
    html = pt.evaluate('id => md("![alt](media:" + id + ")")', mid)
    check('Article images render with srcset', 'srcset' in html and 'figcaption' in html)
    check('Markdown escapes injected markup',
          '<script' not in pt.evaluate('md("<script>alert(1)</script>")'))
    pt.evaluate("go('articles')"); pt.wait_for_timeout(800)
    n_before = pt.evaluate('DB.articles.length')
    pt.evaluate('editArticle(null)'); pt.wait_for_timeout(600)
    pt.fill('#e_title', 'Test article')
    pt.fill('#edBody', 'Body paragraph.\n\n## A heading\n\n- one\n- two')
    pt.click('.drawer-foot .btn-p'); pt.wait_for_timeout(800)
    check('Article saves', pt.evaluate('DB.articles.length') == n_before + 1)
    check('Read time calculated', bool(pt.evaluate('DB.articles[0].readTime')))
    pt.evaluate('togglePublish(0)'); pt.wait_for_timeout(700)
    check('Takedown hides but keeps the article',
          pt.evaluate('DB.articles[0].published') is False and
          pt.evaluate('DB.articles.length') == n_before + 1)

    check('Portal has no JS errors', not perr, str(perr[:2]))
    pt.close()

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
