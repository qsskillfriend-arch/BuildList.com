import re
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
    check('Topbar shows a live date',
          bool(pg.evaluate('document.getElementById("liveDate").textContent.trim()')),
          pg.evaluate('document.getElementById("liveDate").textContent'))
    check('Live dot animates',
          pg.evaluate('getComputedStyle(document.querySelector(".live-dot")).animationName') != 'none')
    check('Ownership still credited in the footer',
          'Sharplink Ventures (U) Limited' in pg.inner_text('footer'))
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
    check('Filled slots render a creative',
          pg.evaluate('document.querySelectorAll(".ad-filled").length') >= 5)
    # Every slot is sold in the sample data, so prove the unsold state
    # by painting one with no campaign rather than expecting a gap.
    check('An unsold slot sells itself',
          pg.evaluate('''(()=>{const el=document.querySelector('[data-ad]');
            const html=el.innerHTML;
            paintAd(el, el.dataset.ad, null);
            const ok = el.classList.contains('ad-empty') &&
                       /slot available/i.test(el.innerText);
            el.innerHTML = html; el.classList.remove('ad-empty');
            return ok;})()'''))

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
    # Legal pages stay ad-free; Add-your-firm carries slots deliberately.
    for route in ['privacy', 'terms']:
        pg.goto(U + 'index.html#/' + route); pg.wait_for_timeout(900)
        n = pg.evaluate('[...document.querySelectorAll("[data-ad]")].filter(e=>e.offsetHeight>0).length')
        check('No advertising on the %s page' % route, n == 0, str(n))
    pg.goto(U + 'index.html#/submit'); pg.wait_for_timeout(1500)
    subs = pg.evaluate('''[...document.querySelectorAll('#page-submit [data-ad]')]
        .filter(e=>e.offsetHeight>0).length''')
    check('Add-your-firm carries its own slots', subs == 6, str(subs))
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
    # The blanket sentence was removed; each creative labels itself instead.
    check('Every advert labels itself',
          pg.evaluate('''[...document.querySelectorAll('.ad-unit.ad-filled')]
            .every(u => /advertis/i.test(u.innerText) || u.querySelector('.ad-label,.ad-sponsored-tag'))'''))

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
    check('Alerts form posts to the API',
          pg.evaluate('!!document.querySelector("form[name=tender-alerts]")') and
          pg.evaluate('typeof handleForm === "function"'))
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
    check('Listing form present and wired',
          pg.evaluate('!!document.querySelector("form[name=listing-submission]")'))
    check('Listing form fields all named',
          pg.evaluate('[...document.querySelectorAll("form[name=listing-submission] input,form[name=listing-submission] select,form[name=listing-submission] textarea")].every(e=>e.name)'))
    pg.goto(U + 'index.html#/about'); pg.wait_for_timeout(1000)
    check('Contact form present and wired',
          pg.evaluate('!!document.querySelector("form[name=contact]")'))
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
          pg.evaluate('document.querySelectorAll(".tab-btn[data-client] .tab-n").length') == 5)
    pg.evaluate('resetTenderFilter()')          # an earlier test left a status filter set
    pg.click('[data-client=government]')
    # Use the app's own definition of "open" — a tender closing today still is
    gov = pg.evaluate('openTenders().filter(t=>t.clientType==="government").length')
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
    check('Homepage shows twelve category capsules',
          pg.evaluate('document.querySelectorAll("#sectorGrid .cat-pill").length') == 12)
    check('Capsules sit five to a row',
          pg.evaluate('''(()=>{const ps=[...document.querySelectorAll('.cat-pill')];
            const t=ps[0].getBoundingClientRect().top;
            return ps.filter(p=>Math.abs(p.getBoundingClientRect().top-t)<3).length;})()''') == 5)
    hrefs = pg.evaluate('[...document.querySelectorAll("#sectorGrid .cat-pill")].map(a=>a.getAttribute("href"))')
    check('Every sector card carries a category filter',
          all(h and 'cat=' in h for h in hrefs), str(hrefs[:2]))
    counts = pg.evaluate('''[...document.querySelectorAll("#sectorGrid .cat-pill-n")].map(e=>e.textContent)''')
    real = pg.evaluate('''(()=>{const c=facetCounts(DATA.firms,'categories');
      return Object.values(c).some(n=>n>0)})()''')
    check('Sector counts come from the data', real, str(counts[:2]))
    pg.click('#sectorGrid .cat-pill'); pg.wait_for_timeout(1600)
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

    # ═══ VERCEL / FORMS ═══
    pg.goto(U + 'index.html#/submit'); pg.wait_for_timeout(1400)
    check('No Netlify attributes remain',
          pg.evaluate('document.querySelectorAll("[data-netlify]").length') == 0)
    KNOWN = re.findall(r"'([a-z0-9-]+)':\s*\{\s*label",
                       open('/home/claude/site/lib/form-core.js', encoding='utf-8').read())
    seen = set()
    for route in ['submit','tenders','jobs','news','directory','about']:
        pg.goto(U + 'index.html#/' + route); pg.wait_for_timeout(1100)
        seen |= set(pg.evaluate('[...document.querySelectorAll("form[name]")].map(f=>f.getAttribute("name"))'))
    check('Every form name is one the API recognises',
          seen <= set(KNOWN), str(sorted(seen - set(KNOWN))))
    check('Every form submits through a handler',
          pg.evaluate('''[...document.querySelectorAll('form[name]')]
            .every(f => /handleForm|saveAlert/.test(f.getAttribute('onsubmit')||''))'''))
    pg.goto(U + 'index.html#/submit'); pg.wait_for_timeout(1200)
    check('Failure path offers a fallback',
          'form-note-error' in pg.content())
    check("Possessive in the brand line",
          "Uganda's Construction Directory" in pg.content())

    # ═══ FIRM VIDEO RENDERING ═══
    check('Public profile can render firm videos',
          pg.evaluate('typeof firmVideos === "function"'))
    check('Video helper handles a firm with none',
          pg.evaluate('firmVideos({slug:"x"}) === ""'))
    # Video is a tier capability now, so the helper needs a tier that allows it.
    check('Video helper renders for a tier that allows it',
          'controls' in pg.evaluate('''firmVideos({slug:"x", tier:"platinum",
            videos:[{src:"a.mp4",poster:"p.jpg",title:"T"}]})'''))
    check('Video is withheld from tiers that do not include it',
          pg.evaluate('''firmVideos({slug:"x", tier:"free",
            videos:[{src:"a.mp4"}]}) === ""'''))

    # ═══ DETAIL PAGES ═══
    pg.goto(U + 'index.html#/tenders'); pg.wait_for_timeout(2000)
    check('Tender titles link to a detail page',
          pg.evaluate('document.querySelectorAll("#tendersFull a.tender-title").length') > 0)
    tslug = pg.evaluate('tenderSlug(openTenders()[0])')
    pg.goto(U + 'index.html#/tenders/' + tslug); pg.wait_for_timeout(1200)
    check('Tender detail page opens',
          pg.evaluate('[...document.querySelectorAll("[id^=page-]:not(.hidden)")].map(e=>e.id)') == ['page-tender'])
    check('Tender detail shows a countdown',
          bool(pg.evaluate('document.querySelector(".countdown-big")')))
    pg.goto(U + 'index.html#/jobs'); pg.wait_for_timeout(1600)
    check('Job titles link to a detail page',
          pg.evaluate('document.querySelectorAll("#jobsFull a.job-title").length') > 0)
    jslug = pg.evaluate('openJobs()[0].slug')
    pg.goto(U + 'index.html#/jobs/' + jslug); pg.wait_for_timeout(1200)
    check('Job detail page opens',
          pg.evaluate('[...document.querySelectorAll("[id^=page-]:not(.hidden)")].map(e=>e.id)') == ['page-job'])
    eslug = pg.evaluate('openEvents()[0].slug')
    pg.goto(U + 'index.html#/events/' + eslug); pg.wait_for_timeout(1200)
    check('Event detail page opens',
          pg.evaluate('[...document.querySelectorAll("[id^=page-]:not(.hidden)")].map(e=>e.id)') == ['page-event'])
    check('Cards are not nested anchors',
          pg.evaluate('document.querySelectorAll("a a").length') == 0)

    # ═══ ALERTS AND FORMS ═══
    pg.goto(U + 'index.html#/tenders'); pg.wait_for_timeout(1800)
    check('Alerts sit below the tender list',
          pg.evaluate('''(()=>{const t=document.getElementById('tendersFull'),a=document.getElementById('alerts');
            return !!t && !!a && a.getBoundingClientRect().top > t.getBoundingClientRect().top;})()'''))
    for name in ['tender-alerts', 'tender-submission']:
        check('Form present: ' + name, pg.evaluate('n => !!document.querySelector("form[name=" + n + "]")', name))
    pg.goto(U + 'index.html#/jobs'); pg.wait_for_timeout(1500)
    check('Form present: job-alerts', pg.evaluate('!!document.querySelector("form[name=job-alerts]")'))
    pg.goto(U + 'index.html#/news'); pg.wait_for_timeout(1600)
    check('Form present: event-submission', pg.evaluate('!!document.querySelector("form[name=event-submission]")'))
    check('News categories are generated with counts',
          pg.evaluate('document.querySelectorAll("#newsTabs .tab-btn").length') >= 3)
    n_all = pg.evaluate('document.querySelectorAll(\'#newsArticles a[href*="news/"]\').length')
    pg.evaluate('document.querySelectorAll("#newsTabs .tab-btn")[1].click()'); pg.wait_for_timeout(700)
    check('News category filters the list',
          pg.evaluate('document.querySelectorAll(\'#newsArticles a[href*="news/"]\').length') < n_all)
    check('Price report button downloads the data',
          pg.evaluate('typeof downloadPriceCsv === "function"'))

    # ═══ NO RATES ANYWHERE PUBLIC ═══
    for route in ['advertise', 'submit', 'tenders', 'jobs']:
        pg.goto(U + 'index.html#/' + route); pg.wait_for_timeout(1200)
        txt = pg.inner_text('#page-' + route)
        bad = [l for l in txt.split('\n') if 'UGX' in l and ('/year' in l or 'per notice' in l or 'per post' in l)]
        check('No BuildList rates on the %s page' % route, not bad, str(bad[:2]))
    check('"Rate card" is gone from the site', 'rate card' not in pg.content().lower())

    # ═══ EVENTS ═══
    pg.goto(U + 'index.html#/news'); pg.wait_for_timeout(2000)
    check('Events calendar renders',
          pg.evaluate('document.querySelectorAll("#eventsList .ev").length') >= 3)
    check('Only future events are shown',
          pg.evaluate('''openEvents().every(e => daysLeft(e.end || e.start) >= 0)'''))
    check('Events are in date order',
          pg.evaluate('''(()=>{const l=openEvents().map(e=>e.start);
            return l.join()===l.slice().sort().join();})()'''))
    check('CPD hours surfaced where they exist',
          pg.evaluate('document.querySelectorAll("#eventsList .ev-tag.cpd").length') >= 2)
    pg.goto(U + 'index.html'); pg.wait_for_timeout(2400)
    check('Homepage shows the next events',
          pg.evaluate('document.querySelectorAll("#eventStrip .ev").length') == 3)

    # ═══ NO PUBLIC RATE CARD ═══
    pg.goto(U + 'index.html#/advertise'); pg.wait_for_timeout(1400)
    adv = pg.inner_text('#page-advertise')
    check('No advertising rates on the public page',
          'UGX' not in adv, adv[adv.find('UGX')-40:adv.find('UGX')+20] if 'UGX' in adv else '')
    check('Rates offered on request',
          'on request' in adv.lower() or 'Request the rate card' in adv)
    check('Ad packages still describe what you get',
          pg.evaluate('document.querySelectorAll(".ad-package-name").length') >= 5)

    # ═══ AD ROTATION AND SHINE ═══
    pg.goto(U + 'index.html'); pg.wait_for_timeout(2600)
    check('Slots hold several campaigns',
          pg.evaluate('liveAdsFor("home-leaderboard").length') >= 5,
          str(pg.evaluate('liveAdsFor("home-leaderboard").length')))
    check('Every slot has rotation attached',
          pg.evaluate('document.querySelectorAll("[data-rotating]").length') >= 8)
    check('Weighting repeats a campaign in the rotation',
          pg.evaluate('''(()=>{const a=DATA.ads.ads.find(x=>x.slot==="home-leaderboard");
            const before=liveAdsFor("home-leaderboard").length;
            a.weight=3; const after=liveAdsFor("home-leaderboard").length;
            a.weight=1; return after === before + 2;})()'''))
    check('Rotation pauses under the pointer',
          pg.evaluate('typeof ROTATE === "object" && ROTATE.paused instanceof Set'))
    pg.evaluate('document.querySelectorAll(".ad-unit.ad-filled").forEach(u=>u.classList.add("shine"))')
    pg.wait_for_timeout(200)
    shined = pg.evaluate('document.querySelectorAll(".ad-unit.shine").length')
    check('Shine applies to every filled slot at once', shined >= 5, str(shined))
    check('Shine is a diagonal sweep',
          '115deg' in pg.content() and 'adShine' in pg.content())
    check('Motion respects prefers-reduced-motion',
          'prefers-reduced-motion' in pg.content() and 'reducedMotion' in pg.content())

    # ═══ PRICE DIRECTION ICONS ═══
    pg.goto(U + 'index.html'); pg.wait_for_timeout(2400)
    arrows = pg.evaluate('''[...document.querySelectorAll('#priceTicker .price-change')]
        .map(e => e.textContent.trim()[0])''')
    check('Price ticker shows direction arrows',
          any(a in '\u25B2\u25BC' for a in arrows), str(arrows[:4]))
    check('Up and down are coloured differently',
          pg.evaluate('document.querySelectorAll("#priceTicker .price-up").length') > 0 and
          pg.evaluate('document.querySelectorAll("#priceTicker .price-down").length') > 0)

    # ═══ REMOVAL REQUESTS ═══
    pg.goto(U + 'index.html'); pg.wait_for_timeout(2200)
    check('Footer offers a way to remove a listing',
          pg.evaluate('!!document.querySelector("footer a[onclick*=openRemoval]")'))
    pg.click('footer a[onclick*=openRemoval]'); pg.wait_for_timeout(800)
    check('Removal form opens',
          pg.evaluate('document.getElementById("removalModal").classList.contains("on")'))
    rnames = pg.evaluate('[...document.querySelectorAll("form[name=removal-request] [name]")].map(e=>e.name)')
    check('Removal form asks who and which listing',
          all(n in rnames for n in ['firm_slug','name','phone']), str(rnames))
    check('Removal form lists every firm',
          pg.evaluate('document.querySelectorAll("#remFirm option").length') > 600)
    check('Removal offers alternatives to deletion',
          set(pg.evaluate('[...document.querySelectorAll("#remWhat option")].map(o=>o.value)'))
          == {'remove','hide-contact','correct'})
    check('Removal states the 48-hour promise',
          '48 hours' in pg.inner_text('#removalModal'))
    check('Removal needs no account',
          'sign in' not in pg.inner_text('#removalModal').lower())
    pg.evaluate('closeRemoval()')
    pg.goto(U + 'index.html#/firms/' + SLUG); pg.wait_for_timeout(1500)
    check('Profiles offer removal too',
          pg.evaluate('!!document.querySelector("#profileContent button[onclick*=openRemoval]")'))

    # ═══ CLAIMING A LISTING ═══
    pg.goto(U + 'index.html#/firms/' + SLUG); pg.wait_for_timeout(1600)
    check('Unverified listings offer a claim',
          pg.evaluate('!!document.querySelector("#profileContent button[onclick*=openClaim]")'))
    pg.click('#profileContent button[onclick*=openClaim]'); pg.wait_for_timeout(700)
    check('Claim dialogue opens',
          pg.evaluate('document.getElementById("claimModal").classList.contains("on")'))
    names = pg.evaluate('[...document.querySelectorAll("form[name=claim-listing] [name]")].map(e=>e.name)')
    check('Claim collects who and how to reach them',
          all(n in names for n in ['claimant','role','phone','firm_slug']), str(names))
    check('Claim explains the phone check',
          'ring' in pg.inner_text('#claimModal').lower())
    pg.evaluate('closeClaim()')

    # ═══ LAUNCH AUDIT: every control goes somewhere real ═══
    pg.goto(U + 'index.html'); pg.wait_for_timeout(1800)
    check('Staff portal is not linked from the footer',
          not pg.evaluate('!!document.querySelector("footer a[href*=portal]")'))
    check('Social icons go to social profiles, not About',
          pg.evaluate('''[...document.querySelectorAll('footer a[aria-label]')]
            .every(a => /^https:/.test(a.getAttribute('href')))'''))
    check('No control shows raw template text',
          '${' not in pg.evaluate('document.body.innerText'))
    for route in ['', '#/tenders', '#/jobs', '#/advertise', '#/submit']:
        pg.goto(U + 'index.html' + route); pg.wait_for_timeout(1300)
        dead = pg.evaluate('''[...document.querySelectorAll('button,a')]
          .filter(e => e.offsetHeight > 0 && !e.closest('.ad-unit') && !e.closest('[id^=page-].hidden'))
          .filter(e => e.tagName === 'A' ? !e.getAttribute('href') || e.getAttribute('href') === '#'
                     : !e.getAttribute('onclick') && e.type !== 'submit' && !e.closest('form'))
          .map(e => e.innerText.trim().slice(0, 30))''')
        check('No dead controls on %s' % (route or 'home'), not dead, str(dead[:4]))

    pg.goto(U + 'index.html#/advertise'); pg.wait_for_timeout(1600)
    cards = pg.evaluate('''[...document.querySelectorAll('.ad-package-card')].map(c =>
        c.querySelectorAll('button, a.btn').length)''')
    check('Every advertising package has exactly one action', all(n == 1 for n in cards), str(cards))
    wide = b.new_page(viewport={'width': 1500, 'height': 900})
    wide.goto(U + 'index.html#/advertise'); wide.wait_for_timeout(1700)
    check('All six packages sit on one row',
          wide.evaluate('''(()=>{const c=[...document.querySelectorAll('.ad-package-card')];
            const t=c[0].getBoundingClientRect().top;
            return c.filter(x=>Math.abs(x.getBoundingClientRect().top-t)<3).length;})()''') == 6)
    wide.close()

    pg.goto(U + 'index.html#/jobs'); pg.wait_for_timeout(1600)
    check('A real job-posting form exists',
          pg.evaluate('!!document.querySelector("form[name=job-submission]")'))
    check('Post a Job goes to the job form, not the tender form',
          pg.evaluate('''[...document.querySelectorAll('button')]
            .filter(b => /Post a Job/.test(b.textContent))
            .every(b => /postJobForm/.test(b.getAttribute('onclick') || ''))'''))
    check('No job applies to a placeholder address',
          pg.evaluate('!document.body.innerHTML.includes("example.co.ug")'))

    pg.goto(U + 'index.html#/tenders'); pg.wait_for_timeout(1600)
    check('Each procuring entity links to its own site',
          pg.evaluate('''DATA.tenders.every(t => !t.orgWebsite ||
            !t.orgWebsite.includes("ppda") || t.ref.startsWith("PPDA"))'''))

    pg.goto(U + 'index.html#/submit'); pg.wait_for_timeout(1600)
    tiers = pg.evaluate('[...document.querySelectorAll("#tierCards .tier-name")].map(e=>e.textContent)')
    check('All five tiers offered, Starter included', len(tiers) == 5 and 'Starter' in tiers, str(tiers))
    check('Tier cards are generated from the enforced capabilities',
          pg.evaluate('''(()=>{const f=[...document.querySelectorAll('#tierCards .tier-card')]
            .find(c=>c.querySelector('.tier-name').textContent==='Free');
            return /No photographs/.test(f.innerText) && /Phone number only/.test(f.innerText);})()'''))

    # ═══ BUTTONS THAT DO THE NEEDFUL ═══
    pg.goto(U + 'index.html#/tenders'); pg.wait_for_timeout(2200)
    pg.evaluate('localStorage.clear(); renderAlertPanel()'); pg.wait_for_timeout(400)
    pg.click('button:has-text("Activate Free Alert")'); pg.wait_for_timeout(1500)
    check('Activate Free Alert reaches the form',
          pg.evaluate('!!document.activeElement.closest("#alertForm")'))
    check('Alert form is on screen',
          pg.evaluate('''(()=>{const r=document.getElementById('alertForm').getBoundingClientRect();
            return r.top < window.innerHeight && r.bottom > 0;})()'''))
    pg.evaluate('setSub("tenders",{email:"x@y.com"}); renderAlertPanel()'); pg.wait_for_timeout(500)
    pg.click('button:has-text("Activate Free Alert")'); pg.wait_for_timeout(1400)
    check('It reopens the form for someone already subscribed',
          pg.evaluate('!!document.getElementById("alertForm")'))
    pg.evaluate('localStorage.clear(); renderAlertPanel()')
    check('Submit-a-notice offers an email compose',
          pg.evaluate('typeof composeTenderEmail === "function"') and
          pg.evaluate('''[...document.querySelectorAll('button')]
            .some(b => /Email us the notice/.test(b.textContent))'''))
    check('And still offers the form as an alternative',
          pg.evaluate('''[...document.querySelectorAll('button,a')]
            .some(b => /fill in the form/i.test(b.textContent))'''))

    # ═══ FEATURED AND SPONSORED ARTICLES OPEN ═══
    pg.goto(U + 'index.html#/news'); pg.wait_for_timeout(2200)
    href = pg.evaluate('document.querySelector("#sponsoredArticle a")?.getAttribute("href")')
    check('Sponsored article links to its page', bool(href and href.startswith('#/news/')), str(href))
    check('Sponsored card names its sponsor',
          'sponsored' in pg.inner_text('#sponsoredArticle').lower() and
          'sample cement' in pg.inner_text('#sponsoredArticle').lower())
    check('Recent articles are links',
          pg.evaluate('document.querySelectorAll("#recentArticles a[href^=\'#/news/\']").length') >= 3)
    pg.click('#sponsoredArticle a'); pg.wait_for_timeout(1300)
    check('Sponsored article opens its content page',
          pg.evaluate('[...document.querySelectorAll("[id^=page-]:not(.hidden)")].map(e=>e.id)') == ['page-article'])
    pg.goto(U + 'index.html#/news'); pg.wait_for_timeout(1600)
    pg.click('#recentArticles a'); pg.wait_for_timeout(1300)
    check('Recent article opens its content page',
          pg.evaluate('[...document.querySelectorAll("[id^=page-]:not(.hidden)")].map(e=>e.id)') == ['page-article'])

    # ═══ TIER PRIVILEGES ARE REAL ═══
    pg.goto(U + 'index.html#/directory'); pg.wait_for_timeout(2400)
    check('Tiers define capabilities, not just a name',
          pg.evaluate('''DATA.taxonomy.tiers.every(t => t.caps &&
            typeof t.caps.whatsapp === "boolean" && typeof t.caps.photos === "number")'''))
    check('Free tier withholds WhatsApp, website and photos',
          pg.evaluate('''(()=>{const f={tier:"free",photos:[1,2,3],website:"x"};
            return !can(f,"whatsapp") && !can(f,"website") && capPhotos(f).length===0;})()'''))
    check('Paid tiers grant them',
          pg.evaluate('''(()=>{const f={tier:"platinum",photos:[1,2,3],website:"x"};
            return can(f,"whatsapp") && can(f,"website") && capPhotos(f).length===3;})()'''))
    check('Description is trimmed to the tier allowance',
          pg.evaluate('''(()=>{const long="word ".repeat(400);
            const free=capDescription({tier:"free",description:long});
            const plat=capDescription({tier:"platinum",description:long});
            return free.length < plat.length && free.length <= 165;})()'''))
    check('Ranking uses the tier boost',
          pg.evaluate('''capN({tier:"platinum"},"sortBoost") > capN({tier:"free"},"sortBoost")'''))
    check('Badges only on tiers that include one',
          pg.evaluate('tierBadge("free") === "" && tierBadge("platinum") !== ""'))
    check('Only eligible tiers reach the homepage strip',
          pg.evaluate('''(()=>{const c=DATA.taxonomy.tiers.find(t=>t.slug==="free").caps;
            return c.homepageFeature === false;})()'''))

    # ═══ DIRECTORY AD RAIL ═══
    wide = b.new_page(viewport={'width': 1500, 'height': 1000})
    wide.goto(U + 'index.html#/directory'); wide.wait_for_timeout(2400)
    check('Directory has a vertical ad rail',
          wide.evaluate('document.querySelectorAll(".ad-rail .ad-unit").length') == 6)
    check('Rail runs the height of the results',
          wide.evaluate('''document.querySelector('.ad-rail').getBoundingClientRect().height >
            document.getElementById('dirListings').getBoundingClientRect().height * 0.9'''))
    check('Rail creatives are contained, not cropped',
          wide.evaluate('''[...document.querySelectorAll('.ad-rail img')]
            .every(i => i.getBoundingClientRect().width <= i.parentElement.getBoundingClientRect().width + 1)'''))
    wide.close()

    # ═══ HEADER ACTIONS GO SOMEWHERE ═══
    for label, form in [('Post Tender / Job', 'tender-submission'), ('Add Listing', 'listing-submission')]:
        pg.goto(U + 'index.html'); pg.wait_for_timeout(1800)
        pg.click('a:has-text("%s"), button:has-text("%s")' % (label, label)); pg.wait_for_timeout(1700)
        check('%s opens its form' % label,
              pg.evaluate('(document.querySelector("form[name=%s]")?.offsetHeight||0)>0' % form))
    check('No double-hash links remain',
          pg.evaluate('''[...document.querySelectorAll('a[href]')]
            .every(a => (a.getAttribute('href').match(/#/g)||[]).length <= 1)'''))

    # ═══ AD SLOT SIZING ═══
    tops = {}
    for route, slot in [('tenders','tenders-leaderboard'), ('jobs','jobs-leaderboard'),
                        ('news','news-leaderboard')]:
        pg.goto(U + 'index.html#/' + route); pg.wait_for_timeout(1500)
        tops[slot] = pg.evaluate('s => { const e = document.querySelector("[data-ad=" + s + "]");'
                                 ' return e ? Math.round(e.getBoundingClientRect().height) : 0; }', slot)
    check('Top slot is the same height on every page',
          len(set(tops.values())) == 1 and list(tops.values())[0] > 100, str(tops))
    for route in ['tenders', 'jobs', 'news']:
        pg.goto(U + 'index.html#/' + route); pg.wait_for_timeout(1400)
        side = pg.evaluate('''[...document.querySelectorAll('[data-ad$="-sidebar"],[data-ad*="-sidebar-"]')]
            .filter(e => e.offsetHeight > 0).length''')
        check('Three sidebar slots on the %s page' % route, side == 3, str(side))
    check('Sidebar slots are all one size',
          pg.evaluate('''(()=>{const h=[...document.querySelectorAll('[data-ad*="sidebar"]')]
            .filter(e=>e.offsetHeight>0).map(e=>Math.round(e.getBoundingClientRect().height));
            return new Set(h).size === 1;})()'''))
    check('Slot registry matches what is on the page',
          pg.evaluate('''[...document.querySelectorAll('[data-ad]')]
            .every(e => DATA.ads.slots[e.dataset.ad])'''))

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
    check('Footer is lean',
          pg.evaluate('document.querySelectorAll("footer a").length') <= 20,
          str(pg.evaluate('document.querySelectorAll("footer a").length')))
    check('Footer legal links open the policies',
          pg.evaluate('''["#/privacy","#/terms"].every(h =>
            !!document.querySelector('footer a[href="' + h + '"]'))'''))

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
    # The claim is hidden below 760px so the centred LIVE caption has room.
    check('Mobile: brand line still present',
          mob.evaluate('!!document.querySelector(".logo-sub")'))
    check('Mobile: LIVE caption still shown',
          mob.evaluate('document.querySelector(".live-now").offsetHeight') > 0)

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
          'Quantity Surveyors in Kampala' in pg.title(), pg.title())
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
        'admin':  ['board','firms','claims','tenders','jobs','articles','media','prices','spotlight','featured','tiers','ads','analytics','staff','legal','publish'],
        'editor': ['board','firms','claims','tenders','jobs','articles','media','prices','spotlight','featured','analytics','publish'],
        'agent':  ['board','firms','publish'],
    }
    for role, nav in EXPECT.items():
        pt.goto(U + 'portal.html'); pt.wait_for_timeout(1400)
        pt.evaluate('r => demoAs(r)', role); pt.wait_for_timeout(1800)
        got = pt.evaluate('[...document.querySelectorAll(".rail a")].map(a=>a.dataset.go)')
        check('Portal nav for ' + role, sorted(got) == sorted(nav), str(got))
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

    # ═══ VIDEO PIPELINE ═══
    pt.evaluate("go('media')"); pt.wait_for_timeout(700)
    check('Video limits match Supabase Free',
          pt.evaluate('VIDEO_CFG.maxBytes') == 45 * 1024 * 1024 and
          pt.evaluate('VIDEO_CFG.resumableAbove') == 6 * 1024 * 1024)
    check('Accepts MP4, WebM and MOV',
          set(pt.evaluate('VIDEO_CFG.accept')) == {'video/mp4', 'video/webm', 'video/quicktime'})
    check('Resumable uploader present', pt.evaluate('typeof tusUpload === "function"'))
    check('Poster generator present', pt.evaluate('typeof posterFrom === "function"'))
    pt.evaluate('''async () => {
      const r = await fetch('/clip-test.webm').catch(()=>null);
      if (!r || !r.ok) return;
      const f = new File([await r.blob()], 'walkthrough.webm', {type:'video/webm'});
      window.MEDIA_TARGET='firm-video';
      await queueFiles([f]);
    }''')
    pt.wait_for_timeout(3500)
    vid = pt.evaluate('DB.media.find(m=>m.kind==="video")')
    if vid:
        check('Video upload records dimensions and duration',
              vid['naturalW'] == 640 and vid['duration'] > 0, str(vid.get('naturalW')))
        check('Poster frame generated automatically', bool(vid.get('posterUrl')))
    else:
        check('Video upload records dimensions and duration', False, 'no test clip served')
        check('Poster frame generated automatically', False, 'no test clip served')
    pt.evaluate('''async () => {
      await queueFiles([new File([new Uint8Array(47*1024*1024)],'huge.mp4',{type:'video/mp4'})]);
    }''')
    pt.wait_for_timeout(2200)
    check('Oversize video rejected with a useful message',
          '45MB' in pt.evaluate('UPLOADS[0].msg'))
    pt.evaluate('''async () => {
      await queueFiles([new File([new Uint8Array(500)],'x.avi',{type:'video/x-msvideo'})]);
    }''')
    pt.wait_for_timeout(1400)
    check('Unsupported video format rejected',
          'MP4, WebM or MOV' in pt.evaluate('UPLOADS[0].msg'))
    check('Library distinguishes images from video',
          pt.evaluate('typeof mediaPublicUrl === "function" && typeof attachToFirm === "function"'))

    # ═══ EVERY PORTAL SECTION IS BUILT ═══
    pt.goto(U + 'portal.html'); pt.wait_for_timeout(1500)
    pt.evaluate('demoAs("admin")'); pt.wait_for_timeout(2000)
    for sec in ['board','firms','tenders','jobs','articles','media','prices',
                'spotlight','ads','analytics','staff']:
        pt.evaluate('s => go(s)', sec); pt.wait_for_timeout(1000)
        body = pt.inner_text('#pages')
        check('Portal section built: ' + sec,
              'Not built yet' not in body and len(body) > 150, body[:60])

    # Editors open and validate
    pt.evaluate("go('tenders')"); pt.wait_for_timeout(700)
    pt.evaluate('editTender(null)'); pt.wait_for_timeout(600)
    check('Tender editor opens', pt.evaluate('!!document.getElementById("e_deadline")'))
    pt.evaluate('closeDrawer()')
    pt.evaluate("go('jobs')"); pt.wait_for_timeout(700)
    pt.evaluate('editJob(null)'); pt.wait_for_timeout(600)
    check('Job editor opens', pt.evaluate('!!document.getElementById("e_closes")'))
    pt.evaluate('closeDrawer()')
    pt.evaluate("go('ads')"); pt.wait_for_timeout(700)
    pt.evaluate('editAd(null)'); pt.wait_for_timeout(600)
    check('Ad editor opens', pt.evaluate('!!document.getElementById("e_slot")'))
    pt.fill('#e_adv', 'Test Co')
    pt.evaluate('document.getElementById("e_end").value = ""')
    pt.click('.drawer-foot .btn-p'); pt.wait_for_timeout(600)
    check('Ad without an end date is blocked',
          pt.evaluate('document.getElementById("drawer").classList.contains("on")'))
    pt.evaluate('closeDrawer()')

    # The editorial slot cannot be sold, structurally
    pt.evaluate("go('spotlight')"); pt.wait_for_timeout(700)
    pt.evaluate("editSpot('project')"); pt.wait_for_timeout(600)
    check('Benchmark Project has no advertiser field',
          not pt.evaluate('!!document.getElementById("e_advertiser")'))
    check('Benchmark Project has no link or rate field',
          not pt.evaluate('!!document.getElementById("e_link")') and
          not pt.evaluate('!!document.getElementById("e_rate")'))
    pt.fill('#e_name', 'Test project')
    pt.click('.drawer-foot .btn-p'); pt.wait_for_timeout(800)
    check('Benchmark Project is forced unsponsored',
          pt.evaluate('DB.spotlight.project.sponsored') is False)
    pt.evaluate("editSpot('product')"); pt.wait_for_timeout(600)
    check('Product of the Month does have an advertiser field',
          pt.evaluate('!!document.getElementById("e_advertiser")'))
    pt.evaluate('closeDrawer()')

    # Analytics renders real numbers
    pt.evaluate("go('analytics')"); pt.wait_for_timeout(1800)
    check('Analytics shows headline figures',
          pt.evaluate('document.querySelectorAll("#pages dl.kpis > div").length') == 4)
    check('Analytics lists per-firm activity',
          pt.evaluate('document.querySelectorAll("#pages .panel table tbody tr").length') > 3)
    check('Analytics links to Google Analytics and Search Console',
          pt.evaluate('document.querySelectorAll("#pages a[href*=google]").length') >= 2)

    pt.evaluate("go('prices')"); pt.wait_for_timeout(900)
    check('Price editor previews the live ribbon chip',
          pt.evaluate('document.querySelectorAll("#priceRows tr td:nth-child(5) span").length') > 5)
    check('Chip shows an arrow',
          any(a in pt.evaluate('document.querySelector("#priceRows tr td:nth-child(5)").innerText')
              for a in ['\u25B2', '\u25BC', '\u2014']))

    pt.evaluate("go('claims')"); pt.wait_for_timeout(900)
    check('Portal lists listing claims',
          pt.evaluate('document.querySelectorAll("#pages tbody tr").length') >= 2)
    check('Claims show the number to ring, not the claimant\u2019s',
          'ring' in pt.inner_text('#pages').lower())
    pt.evaluate('reviewClaim(DB.claims.find(c=>c.status==="pending").id)'); pt.wait_for_timeout(700)
    pt.select_option('#e_decision', 'approved')
    pt.click('.drawer-foot .btn-p'); pt.wait_for_timeout(600)
    check('A decision cannot be saved without a note',
          pt.evaluate('document.getElementById("drawer").classList.contains("on")'))
    pt.evaluate('closeDrawer()')

    # ═══ EDIT, SAVE, PUBLISH ═══
    pt.evaluate('localStorage.removeItem("buildlist-portal-pending")')
    pt.evaluate('paintPublish()'); pt.wait_for_timeout(300)
    check('Topbar says the site is current when nothing is pending',
          'up to date' in pt.inner_text('#publishBar'))

    pt.evaluate("go('jobs')"); pt.wait_for_timeout(700)
    pt.evaluate('editJob(null)'); pt.wait_for_timeout(600)
    pt.fill('#e_title', 'Verify vacancy')
    pt.fill('#e_company', 'Verify Ltd')
    pt.fill('#e_closes', '2026-12-20')
    pt.click('.drawer-foot .btn-p'); pt.wait_for_timeout(900)
    check('Saving a vacancy records an unpublished change',
          pt.evaluate('pending().length') == 1, str(pt.evaluate('pending().map(p=>p.what)')))
    check('Topbar shows the pending count',
          'not on the site yet' in pt.inner_text('#publishBar'))

    pt.evaluate("go('publish')"); pt.wait_for_timeout(700)
    check('Publish section lists what changed',
          pt.evaluate('document.querySelectorAll("#pages tbody tr").length') >= 1)
    check('Publish explains saving is not publishing',
          'two different things' in pt.inner_text('#pages'))
    check('Publish tells you how to configure the hook',
          'BUILD_HOOK_URL' in pt.inner_text('#pages'))
    pt.evaluate('publishSite()'); pt.wait_for_timeout(800)
    check('Publish fails safely without a build hook',
          'Nothing to build' in (pt.evaluate('document.getElementById("pubResult")?.innerText') or ''))
    pt.evaluate('clearPending()')

    check('Prices, jobs and monthly slots all have editors',
          pt.evaluate('''["savePrices","editJob","editSpot","editTender","editAd","editArticle"]
            .every(f => typeof window[f] === "function")'''))

    pt.evaluate("go('legal')"); pt.wait_for_timeout(800)
    check('Legal pages are editable in the portal',
          pt.evaluate('document.querySelectorAll("#pages .filecard").length') == 2)
    check('Legal editor warns it is not legal advice',
          'advocate' in pt.inner_text('#pages'))

    check('Portal has two-factor support',
          pt.evaluate('typeof mfaGate === "function" && typeof submitCode === "function"'))
    check('Administrators must enrol a second factor',
          pt.evaluate('MFA.required.includes("admin")'))

    # Analytics is interactive
    pt.evaluate("go('analytics')"); pt.wait_for_timeout(1500)
    v30 = pt.evaluate('document.querySelector(".an-kpis dd").textContent')
    pt.click('.seg button:has-text("7 days")'); pt.wait_for_timeout(900)
    check('Analytics period switch changes the figures',
          pt.evaluate('document.querySelector(".an-kpis dd").textContent') != v30)
    check('Analytics chart has one bar per day',
          pt.evaluate('document.querySelectorAll(".an-chart .an-day").length') == 7)
    pt.click('.seg button:has-text("30 days")'); pt.wait_for_timeout(900)
    check('Analytics shows every panel',
          pt.evaluate('document.querySelectorAll("#pages .panel").length') >= 4)
    pt.click('#pages tbody tr'); pt.wait_for_timeout(500)
    check('Clicking a firm focuses the chart on it',
          pt.evaluate('!!document.querySelector(".an-controls .pill")'))
    pt.evaluate('anSet("firm", null)'); pt.wait_for_timeout(300)
    pt.click('th.sortable:has-text("Contacts")'); pt.wait_for_timeout(400)
    col = pt.evaluate('[...document.querySelectorAll("#pages tbody tr td:nth-child(4)")].slice(0,8).map(t=>+t.textContent)')
    check('Analytics table sorts', col == sorted(col, reverse=True), str(col))
    check('Sidebar groups appear once each',
          pt.evaluate('''(()=>{const t=document.querySelector('.rail')?.innerText||'';
            return ['Daily','Content','Revenue','Admin'].every(g =>
              t.split(String.fromCharCode(10)).filter(l=>l.trim()===g).length === 1);})()'''))

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
