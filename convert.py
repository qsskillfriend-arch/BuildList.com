# -*- coding: utf-8 -*-
"""Convert BuildList_All_Listings.xlsx into data/firms.json + expanded taxonomy."""
import openpyxl, json, io, re, collections

SRC = '/mnt/user-data/uploads/BuildList_All_Listings.xlsx'
wb = openpyxl.load_workbook(SRC, data_only=True)

# ── 1. Harvest descriptions from the per-category sheets ──────────
# The master sheet lost them; the category sheets still have 210.
desc_by_id = {}
for name in wb.sheetnames:
    if name in ('All Listings', 'Summary', 'Kampala Only'):
        continue
    s = wb[name]
    h = [c.value for c in s[1]]
    idxs = [i for i, v in enumerate(h) if v == 'Description']
    did = h.index('Directory ID')
    for r in s.iter_rows(min_row=2, values_only=True):
        if not r[did]:
            continue
        for i in idxs:
            if i < len(r) and r[i]:
                desc_by_id[r[did]] = str(r[i]).strip()
                break

ws = wb['All Listings']
hdr = [c.value for c in ws[1]]
rows = [dict(zip(hdr, r)) for r in ws.iter_rows(min_row=2, values_only=True) if r[0]]

# ── 2. Taxonomy ───────────────────────────────────────────────────
CATS = [
  ('architecture-design',        'Architecture & Design',                   'Design'),
  ('quantity-surveying',         'Quantity Surveying',                      'Professionals'),
  ('civil-structural',           'Civil & Structural Engineering',          'Professionals'),
  ('land-surveying',             'Land Surveying',                          'Professionals'),
  ('property-valuers',           'Property Valuers',                        'Professionals'),
  ('urban-planning',             'Urban & Town Planning',                   'Professionals'),
  ('general-contracting',        'General Contracting',                     'Contractors'),
  ('electrical-contracting',     'Electrical Contracting',                  'Contractors'),
  ('plumbing-fire',              'Plumbing & Fire Fighting',                'Contractors'),
  ('hvac',                       'Heating, Ventilation & Air Conditioning', 'Contractors'),
  ('structural-steel',           'Structural Steel Design',                 'Contractors'),
  ('landscaping',                'Landscaping & External Works',            'Contractors'),
  ('building-management',        'Building Management Systems',             'Services'),
  ('ict-network',                'ICT & Network Infrastructure',            'Services'),
  ('facility-management',        'Facility Management',                     'Services'),
  ('health-safety',              'Health & Safety Consulting',              'Services'),
  ('environmental',              'Environmental & Sustainability',          'Services'),
  ('real-estate-development',    'Real Estate Development',                 'Development'),
]
CAT_MAP = {
  'Architecture & Design': 'architecture-design',
  'Building Management Systems': 'building-management',
  'Civil & Structural Engineering': 'civil-structural',
  'Electrical Contracting': 'electrical-contracting',
  'Environmental & Sustainability Consulting': 'environmental',
  'Environmental & Sustainability': 'environmental',
  'Facility Managers': 'facility-management',
  'General Contracting': 'general-contracting',
  'Health & Safety Consulting': 'health-safety',
  'Heating, Ventilation & Air Conditioning': 'hvac',
  'ICT & Network Infrastructure': 'ict-network',
  'Land Surveying': 'land-surveying',
  'Landscaping & External Works': 'landscaping',
  'Plumbing & Fire Fighting': 'plumbing-fire',
  'Property Valuers': 'property-valuers',
  'Quantity Surveying': 'quantity-surveying',
  'Real Estate Development': 'real-estate-development',
  'Structural Steel Design': 'structural-steel',
  'Urban & Town Planning': 'urban-planning',
}

# What each category actually does, for derived descriptions.
CAT_BLURB = {
 'architecture-design':     'Architectural design practice',
 'quantity-surveying':      'Quantity surveying and cost consultancy',
 'civil-structural':        'Civil and structural engineering consultancy',
 'land-surveying':          'Land and geomatics surveying firm',
 'property-valuers':        'Property valuation and estate surveying firm',
 'urban-planning':          'Urban, town and spatial planning consultancy',
 'general-contracting':     'Building and civil works contractor',
 'electrical-contracting':  'Electrical installation and contracting firm',
 'plumbing-fire':           'Plumbing and fire protection contractor',
 'hvac':                    'HVAC and refrigeration contractor',
 'structural-steel':        'Structural steel fabrication and engineering firm',
 'landscaping':             'Landscaping and external works contractor',
 'building-management':     'Building management systems and automation specialist',
 'ict-network':             'ICT and network infrastructure contractor',
 'facility-management':     'Facility and property management company',
 'health-safety':           'Occupational health and safety consultancy',
 'environmental':           'Environmental and sustainability consultancy',
 'real-estate-development': 'Property developer',
}

DISTRICTS = ['Kampala','Wakiso','Mukono','Jinja','Entebbe','Mbarara','Gulu','Hoima',
             'Kayunga','Kabale','Tororo','Luweero','Bushenyi','Busia','Mbale']

# ── 3. Geocoding by Kampala neighbourhood ─────────────────────────
AREAS = {
 'nakasero':(0.3230,32.5810),'kololo':(0.3350,32.5950),'ntinda':(0.3580,32.6130),
 'bugolobi':(0.3170,32.6180),'industrial area':(0.3120,32.6020),'wandegeya':(0.3350,32.5700),
 'mengo':(0.3010,32.5590),'nsambya':(0.2970,32.5880),'kabalagala':(0.3020,32.6030),
 'muyenga':(0.2930,32.6120),'kansanga':(0.2890,32.6100),'ggaba':(0.2760,32.6270),
 'naguru':(0.3380,32.6070),'bukoto':(0.3470,32.6000),'kisaasi':(0.3650,32.6090),
 'kyanja':(0.3760,32.6100),'najjera':(0.3760,32.6360),'kiira':(0.3900,32.6500),
 'kireka':(0.3450,32.6620),'bweyogerere':(0.3540,32.6720),'seeta':(0.3610,32.6960),
 'namanve':(0.3540,32.7020),'kawempe':(0.3800,32.5570),'kazo':(0.3760,32.5500),
 'kyebando':(0.3620,32.5750),'mulago':(0.3440,32.5760),'makerere':(0.3320,32.5680),
 'kamwokya':(0.3400,32.5860),'kanjokya':(0.3390,32.5870),'old kampala':(0.3150,32.5650),
 'kikuubo':(0.3130,32.5730),'nakawa':(0.3320,32.6220),'luzira':(0.3060,32.6470),
 'mutundwe':(0.2980,32.5280),'nalukolongo':(0.2890,32.5350),'ndeeba':(0.2950,32.5600),
 'katwe':(0.3000,32.5730),'kibuye':(0.2930,32.5680),'najjanankumbi':(0.2800,32.5570),
 'kisenyi':(0.3130,32.5680),'kampala road':(0.3150,32.5820),'parliament avenue':(0.3170,32.5860),
 'nkrumah':(0.3160,32.5780),'station road':(0.3180,32.5800),'jinja road':(0.3240,32.5970),
 'entebbe road':(0.2900,32.5600),'gayaza':(0.4200,32.6100),'matugga':(0.4530,32.5420),
 'kyaliwajjala':(0.3800,32.6480),'namugongo':(0.3860,32.6740),'kulambiro':(0.3700,32.6020),
 'bwebajja':(0.1420,32.5250),'kitende':(0.1650,32.5300),'munyonyo':(0.2660,32.6180),
 'nateete':(0.3010,32.5390),'rubaga':(0.3050,32.5560),'kawanda':(0.4160,32.5390),
}
DISTRICT_PT = {
 'kampala':(0.3476,32.5825),'wakiso':(0.4044,32.4594),'mukono':(0.3533,32.7553),
 'jinja':(0.4244,33.2041),'entebbe':(0.0512,32.4637),'mbarara':(-0.6072,30.6545),
 'gulu':(2.7746,32.2990),'hoima':(1.4353,31.3520),'kayunga':(0.7025,32.8880),
 'kabale':(-1.2490,29.9897),'tororo':(0.6928,34.1808),'luweero':(0.8490,32.4730),
 'bushenyi':(-0.5857,30.2073),'busia':(0.4644,34.0920),'mbale':(1.0821,34.1750),
}

def geocode(address, region):
    a = (address or '').lower()
    for key, pt in AREAS.items():
        if key in a:
            return pt[0], pt[1], 'area'
    pt = DISTRICT_PT.get((region or '').lower(), DISTRICT_PT['kampala'])
    return pt[0], pt[1], 'district'

# ── 4. Helpers ────────────────────────────────────────────────────
def slugify(s):
    s = re.sub(r'\(.*?\)', ' ', str(s))
    s = s.lower().replace('&', ' and ')
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = re.sub(r'-(ltd|limited|co|company|u|uganda)$', '', s)
    return s[:70].strip('-')

def clean_phone(p):
    if not p: return ''
    p = re.sub(r'[^\d+]', '', str(p))
    if p.startswith('0') and len(p) >= 9: p = '+256' + p[1:]
    if p.startswith('256'): p = '+' + p
    return p if p.startswith('+') else ''

def clean_site(w):
    w = str(w or '').strip()
    if not w or w in ('-', 'n/a'): return ''
    if not w.startswith('http'): w = 'https://' + w.lstrip('/')
    return w

def clean_email(e):
    e = str(e or '').strip().lower()
    return e if '@' in e and ' ' not in e else ''

def tidy_area(address, region):
    """Short human-readable area for the listing card."""
    a = (address or '').strip()
    if not a: return region
    for key in AREAS:
        if key in a.lower():
            nice = key.title()
            return nice if region.lower() in a.lower() or nice == region else nice + ', ' + region
    first = re.split(r'[,\n]', a)[0].strip()
    first = re.sub(r'^(plot|p\.?o\.? box)\s*[\w/\-]*\s*,?\s*', '', first, flags=re.I).strip()
    return (first[:44] + ', ' + region) if first else region

# ── 5. Descriptions ───────────────────────────────────────────────
# Two sources, tracked separately so you always know what is evidenced.
#   researched — taken from the firm's own website or a reputable directory
#   derived    — written from the firm's own category and location. True by
#                construction, but says nothing the spreadsheet did not.
RESEARCHED = {
 'BL-0001': ("Indigenously owned civil and environmental engineering consultancy operating since 2002, and "
             "the first indigenous engineering firm in Uganda to achieve ISO certification. Services span water "
             "supply and wastewater design, construction supervision, geotechnical assessment, environmental and "
             "social impact assessment, and project management.",
             ['Water supply and wastewater design','Construction supervision','Geotechnical assessment',
              'Environmental and social impact assessment','Project management'], 2002),
 'BL-0003': ("Infrastructural consultancy and civil/structural design firm established in 2009, delivering "
             "buildings, highways, energy and water infrastructure in Uganda and the wider East African region. "
             "Holds ISO 9001, ISO 45001 and ISO 14001 certification and is a member of the Uganda Association of "
             "Consulting Engineers.",
             ['Structural planning and design','Construction supervision','Civil and geotechnical design',
              'Road and highway design','Project management'], 2009),
}

def build_desc(row, cat_slug):
    did = row['Directory ID']
    if did in RESEARCHED:
        d, services, year = RESEARCHED[did]
        return d, services, year, 'researched'

    harvested = desc_by_id.get(did)
    region = row['Region']
    blurb = CAT_BLURB[cat_slug]
    if harvested:
        # Harvested rows read "Specialism. Category blurb based in Region."
        lead = harvested.split('.')[0].strip()
        services = [s.strip() for s in re.split(r',| and ', lead) if 2 < len(s.strip()) < 48][:6]
        return harvested, services, None, 'sheet'

    area = tidy_area(row.get('Address'), region)
    d = '%s based in %s.' % (blurb, area if area != region else region)
    return d, [], None, 'derived'

# ── 6. Build ──────────────────────────────────────────────────────
seen_slugs, firms = {}, []
prov = collections.Counter()

for i, r in enumerate(rows):
    cat = CAT_MAP.get(r['Category'])
    if not cat:
        print('!! unmapped category:', r['Category']); continue

    slug = slugify(r['Name'])
    if slug in seen_slugs:
        seen_slugs[slug] += 1
        slug = '%s-%d' % (slug, seen_slugs[slug])
    else:
        seen_slugs[slug] = 1

    region = r['Region'] if r['Region'] in DISTRICTS else 'Kampala'
    lat, lng, precision = geocode(r.get('Address'), region)
    d, services, year, source = build_desc(r, cat)
    prov[source] += 1

    firms.append({
        'id': i + 1,
        'ref': r['Directory ID'],
        'slug': slug,
        'name': str(r['Name']).strip(),
        'initials': (str(r.get('Code') or '')[:2].upper() or
                     ''.join(w[0] for w in str(r['Name']).split()[:2]).upper()),
        'categories': [cat],
        'district': region.lower(),
        'area': tidy_area(r.get('Address'), region),
        'address': str(r.get('Address') or '').strip(),
        'desc': d,
        'descSource': source,
        'services': services,
        'rating': 0,
        'reviews': 0,
        # Nobody is paying yet and nobody has been checked. Both stay honest
        # until a field agent has visited and a payment has cleared.
        'tier': 'free',
        'sourceTier': str(r.get('Tier') or 'Standard'),
        'status': 'live',
        'accreditations': [],
        'phone': clean_phone(r.get('Phone')),
        'whatsapp': clean_phone(r.get('Phone')),
        'email': clean_email(r.get('Email')),
        'website': clean_site(r.get('Website')),
        'logo': '',
        'photos': [],
        'projects': [],
        'established': year or '',
        'employees': '',
        'verified': False,
        'verifiedDate': None,
        'createdAt': '2026-09-11',
        'lat': lat, 'lng': lng, 'geoPrecision': precision,
    })

# ── 7. Write ──────────────────────────────────────────────────────
io.open('/home/claude/site/data/firms.json', 'w', encoding='utf-8').write(
    json.dumps(firms, indent=2, ensure_ascii=False) + '\n')

tax = json.load(io.open('/home/claude/site/data/taxonomy.json', encoding='utf-8'))
tax['categories'] = [{'slug': s, 'name': n, 'cluster': c} for s, n, c in CATS]
tax['districts'] = [{'slug': d.lower(), 'name': d} for d in DISTRICTS]
io.open('/home/claude/site/data/taxonomy.json', 'w', encoding='utf-8').write(
    json.dumps(tax, indent=2, ensure_ascii=False) + '\n')

print('firms written:', len(firms))
print('description source:', dict(prov))
print('with phone:  ', sum(1 for f in firms if f['phone']))
print('with email:  ', sum(1 for f in firms if f['email']))
print('with website:', sum(1 for f in firms if f['website']))
print('geo precise: ', sum(1 for f in firms if f['geoPrecision'] == 'area'), 'of', len(firms))
print('districts:   ', len(tax['districts']), '| categories:', len(tax['categories']))
