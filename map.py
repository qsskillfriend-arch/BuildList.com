import json
from playwright.sync_api import sync_playwright
U='http://localhost:8899/index.html'
ROUTES=['','#/directory','#/tenders','#/jobs','#/news','#/advertise','#/submit','#/about','#/privacy','#/terms']
JS='''() => [...document.querySelectorAll('a[href],button,[onclick]')]
 .filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height&&!e.closest('[id^=page-].hidden')&&!e.closest('.ad-unit')&&!e.closest('#dirListings')&&!e.closest('.filter-group')})
 .map(e=>{const oc=e.getAttribute('onclick')||'';const fn=(oc.match(/^\\s*(?:return\\s+)?([A-Za-z_$][\\w$]*)\\s*\\(/)||[])[1]||'';
   return {t:(e.innerText||e.getAttribute('aria-label')||e.title||'').trim().replace(/\\s+/g,' ').slice(0,38),
           h:e.getAttribute('href')||'', oc:oc.slice(0,55), fn, exists: fn? typeof window[fn]==='function':null,
           type:e.getAttribute('type')||'', zone: e.closest('header')?'header':e.closest('footer')?'footer':'page'}})'''
out={}
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1500,'height':900})
    pg.add_init_script("try{localStorage.setItem('buildlist-consent',JSON.stringify({choice:'declined',at:Date.now()}))}catch(e){}")
    for r in ROUTES:
        pg.goto(U+r); pg.wait_for_timeout(1300)
        out[r or '#/home']=pg.evaluate(JS)
    b.close()
json.dump(out,open('/tmp/controls.json','w'),indent=1)
seen=set()
for r,items in out.items():
    for c in items:
        k=(c['t'],c['h'],c['oc'],c['zone'])
        if c['zone']!='page' and k in seen: continue
        seen.add(k)
        flag=''
        if c['fn'] and c['exists'] is False: flag='!! MISSING FN'
        elif c['h'] in ('#','') and not c['oc'] and c['type']!='submit': flag='!! NO TARGET'
        print('%-12s %-6s %-38s %-28s %s' % (r if c['zone']=='page' else c['zone'], c['type'] or '', c['t'], (c['h'] or c['oc'])[:28], flag))
