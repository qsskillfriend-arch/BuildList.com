import re, sys
from playwright.sync_api import sync_playwright
U='http://localhost:8899/'
R=[]
def ck(n,c,d=''): R.append((bool(c),n,str(d)[:70]))
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1400,'height':1000})
    errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(U+'index.html'); pg.wait_for_timeout(2500)
    ck('site loads', pg.evaluate('DATA_READY'))

    # legal cautions gone
    for r in ['privacy','terms']:
        pg.goto(U+'index.html#/'+r); pg.wait_for_timeout(1300)
        t=pg.inner_text('#page-'+r).lower()
        ck('no advocate caution on '+r, not any(w in t for w in ['advocate','must be reviewed','working draft','template —']))
    # placeholders
    FILLER=re.compile(r'(\[[A-Za-z ]{2,24}\]|example\.(com|co)|700 000 000|Sample [A-Z][a-z]+|Advertiser \d|placeholder creative|Plot 18)',re.I)
    for r in ['','#/directory','#/tenders','#/jobs','#/news','#/advertise','#/submit','#/about','#/privacy','#/terms']:
        pg.goto(U+'index.html'+r); pg.wait_for_timeout(1200)
        blob=pg.evaluate('document.body.innerText')+' '+' '.join(pg.evaluate('[...document.querySelectorAll("img[alt],a[href]")].map(e=>e.alt||e.getAttribute("href"))'))
        hits=sorted(set(m.group(0) for m in FILLER.finditer(blob)))
        ck('no placeholders on '+(r or 'home'), not hits, hits[:3])

    # tier capabilities
    pg.goto(U+'index.html#/directory'); pg.wait_for_timeout(2200)
    caps=pg.evaluate('''(()=>{const mk=t=>({tier:t,categories:['a','b','c','d','e','f','g'],services:Array(60).fill('s'),
      projects:Array(40).fill({name:'p'}),logo:'l.png',catalogue:'c.pdf',district:'kampala',lat:.5,lng:32.9,
      description:'word '.repeat(2000),photos:Array(120).fill({url:'x'}),videos:[{src:'v.mp4'}]});const o={};
      for(const t of ['free','starter','verified','premium','platinum']){const f=mk(t);
      o[t]={cats:capCats(f).length,serv:capServices(f).length,proj:capProjects(f).length,photos:capPhotos(f).length,
      desc:capDescription(f).length,logo:can(f,'logo'),wa:can(f,'whatsapp'),site:can(f,'website'),
      video:firmVideos(f)!=='',badge:tierBadge(t)!=='',cat:can(f,'catalogue'),reply:can(f,'reviewReply'),
      exact:!pinFor(f).approx,boost:capN(f,'sortBoost'),home:can(f,'homepageFeature')};}return o})()''')
    fr,pl=caps['free'],caps['platinum']
    ck('free withholds every paid capability',
       fr['photos']==0 and not fr['wa'] and not fr['site'] and not fr['logo'] and not fr['video']
       and not fr['badge'] and not fr['cat'] and not fr['reply'] and fr['cats']==1 and fr['serv']==0
       and fr['proj']==0 and not fr['exact'] and fr['boost']==0 and not fr['home'], fr)
    ck('platinum grants them all',
       pl['photos']==100 and pl['wa'] and pl['site'] and pl['logo'] and pl['video'] and pl['badge']
       and pl['cat'] and pl['reply'] and pl['cats']==6 and pl['serv']==50 and pl['proj']==30
       and pl['exact'] and pl['boost']==4 and pl['home'], pl)
    order=['free','starter','verified','premium','platinum']
    for f in ['photos','serv','proj','cats','desc','boost']:
        v=[caps[t][f] for t in order]; ck('%s rises with tier'%f, v==sorted(v), v)
    ck('category counts match the filter',
       pg.evaluate('''DATA.taxonomy.categories.every(c=>(facetCounts(DATA.firms,'categories')[c.slug]||0)===DATA.firms.filter(f=>capCats(f).includes(c.slug)).length)'''))
    ck('22 categories, named as entities',
       pg.evaluate('DATA.taxonomy.categories.length')==22 and
       pg.evaluate("DATA.taxonomy.categories.some(c=>c.name==='Quantity Surveyors')") and
       not pg.evaluate("DATA.taxonomy.categories.some(c=>/Surveying$/.test(c.name))"))

    # reviews on the site
    slug=pg.evaluate('DATA.firms[0].slug')
    pg.goto(U+'index.html#/firms/'+slug); pg.wait_for_timeout(1600)
    ck('any firm can be reviewed', pg.evaluate('!!document.querySelector("#reviews button[onclick^=openReview]")'))
    ck('moderation promise shown', 'checked before they appear' in pg.inner_text('#reviews'))
    pg.click('#reviews button[onclick^=openReview]'); pg.wait_for_timeout(700)
    ck('star picker present', pg.evaluate('document.querySelectorAll(".star-pick button").length')==5)
    names=pg.evaluate('[...document.querySelectorAll("form[name=listing-review] [name]")].map(e=>e.name)')
    ck('review form fields', all(n in names for n in ['rating','review','name','email','firm_slug']), names)
    pg.fill('#revText','They delivered the drawings on time and answered every query from site.')
    pg.fill('#revName','T'); pg.fill('#revEmail','t@t.co')
    pg.click('form[name=listing-review] button[type=submit]'); pg.wait_for_timeout(400)
    ck('review without stars refused', 'Choose a rating' in pg.inner_text('#revMsg'))
    pg.evaluate('closeReview()')

    # portal
    pt=b.new_page(viewport={'width':1440,'height':1000}); perr=[]
    pt.on('pageerror', lambda e: perr.append(str(e))); pt.on('dialog', lambda d: d.accept())
    pt.goto(U+'portal.html'); pt.wait_for_timeout(1500)
    pt.evaluate('demoAs("admin")'); pt.wait_for_timeout(2000)
    for sec in ['board','firms','reviews','claims','tenders','jobs','articles','media','prices',
                'spotlight','featured','tiers','ads','analytics','staff','legal','publish']:
        pt.evaluate('s=>go(s)', sec); pt.wait_for_timeout(800)
        body=pt.inner_text('#pages')
        ck('portal section: '+sec, 'Not built yet' not in body and len(body)>120, body[:40])
    pt.evaluate("go('reviews')"); pt.wait_for_timeout(700)
    n0=pt.evaluate('pendingReviews().length')
    pt.click('.rev-card .btn-p'); pt.wait_for_timeout(600)
    ck('publishing clears the queue', pt.evaluate('pendingReviews().length')==n0-1)
    pt.click('.rev-card .btn-d'); pt.wait_for_timeout(500)
    pt.select_option('#e_reason','fake'); pt.click('.drawer-foot .btn-p'); pt.wait_for_timeout(600)
    ck('rejection records a reason', bool(pt.evaluate('(DB.reviews.find(r=>r.status==="rejected")||{}).reject_reason')))
    pt.evaluate("go('firms')"); pt.wait_for_timeout(700)
    pt.evaluate('editFirm(DB.firms[0].id)'); pt.wait_for_timeout(800)
    ck('firm editor lists 22 categories', pt.evaluate('document.querySelectorAll("#e_cats input").length')==22)
    ck('firm editor has services/projects/logo/catalogue',
       pt.evaluate('["e_services","e_projects","e_logo","e_catalogue"].every(i=>!!document.getElementById(i))'))
    pt.fill('#e_services','One\nTwo\nThree')
    pt.select_option('#e_tier','free'); pt.wait_for_timeout(250); fnote=pt.inner_text('#al_services')
    pt.select_option('#e_tier','premium'); pt.wait_for_timeout(250)
    ck('allowances follow the tier live', 'Not included' in fnote and '3 of 25' in pt.inner_text('#al_services'), fnote)
    pt.evaluate('closeDrawer()')
    pt.evaluate("go('analytics')"); pt.wait_for_timeout(1600)
    ck('analytics panels render', pt.evaluate('document.querySelectorAll("#pages .panel").length')>=4)
    ck('monthly reports listed', pt.evaluate('reportsDue().length')>0)
    ck('report builder real', pt.evaluate('typeof firmReport==="function" && typeof dayChart==="function"'))
    pt.evaluate("go('staff')"); pt.wait_for_timeout(700)
    ck('staff can be invited', pt.evaluate('!!document.getElementById("stInvite")'))
    ck('cannot remove yourself', 'cannot remove yourself' in pt.inner_text('#pages'))
    ck('no portal JS errors', not perr, perr[:1])
    ck('no site JS errors', not errs, errs[:1])
    b.close()
ok=sum(1 for x in R if x[0])
print('='*66)
for good,n,d in R:
    if not good: print('  FAIL  %-44s %s'%(n,d))
print('%d/%d passed'%(ok,len(R)))
