# Images: logos, photographs and ad creatives

There is no upload button on this version, and that is deliberate. Uploads need
a server, a login, storage and moderation — that is Stage 3 of the build guide.
Until then, **images are files in this repository**, and you add them the same
way you add any other file: through GitHub's web interface, no software needed.

The whole workflow is: **put the file here → point a JSON field at it → commit.**

---

## Folders

```
images/
├── logos/   ← firm logos, square
├── firms/   ← photographs of premises, sites, teams
└── ads/     ← advertiser banner creatives
```

Files here ship with the site, so keep them small. A 4 MB photo straight off a
phone will make the page crawl on a 3G connection in Mukono, which is exactly
where your users are.

---

## 1. Adding a firm logo

**Step 1 — prepare the file.**

| Requirement | Value |
|---|---|
| Shape | Square |
| Size | 400 × 400 px |
| Format | PNG (keeps text sharp; supports transparency) |
| File size | Under 60 KB |
| Filename | Exactly the firm's `slug` — `palm-associates-uganda.png` |

Free tools: [squoosh.app](https://squoosh.app) to compress,
[remove.bg](https://remove.bg) if the logo came on a coloured background.

**Step 2 — upload it.** On GitHub open `images/logos/` → **Add file** →
**Upload files** → drag it in → **Commit changes**.

**Step 3 — point the firm at it.** Open `data/firms.json`, find the firm, set:

```json
"logo": "images/logos/palm-associates-uganda.png"
```

Commit. Vercel redeploys in about 30 seconds.

**If the file is missing or the path is wrong, the listing falls back to the
firm's coloured initials.** It never shows a broken-image icon. That is
intentional — you can add logos gradually without any listing ever looking
broken.

To go back to initials, set `"logo": ""`.

---

## 2. Adding firm photographs

Photographs appear as a gallery on the firm's profile page. They are the single
biggest difference between a listing that gets contacted and one that does not —
a photograph of the actual shopfront tells a buyer the business is real.

| Requirement | Value |
|---|---|
| Shape | Landscape, 4:3 |
| Size | 1200 × 900 px |
| Format | JPG (photographs compress far better as JPG than PNG) |
| File size | Under 200 KB |
| Filename | `firmslug-1.jpg`, `firmslug-2.jpg` … |

Upload to `images/firms/`, then in `data/firms.json`:

```json
"photos": [
  { "src": "images/firms/palm-associates-1.jpg",
    "alt": "Shopfront on Kampala Road",
    "caption": "Our Nakasero office" },
  { "src": "images/firms/palm-associates-2.jpg",
    "alt": "Team on site at Nakawa",
    "caption": "Site supervision, Nakawa" }
]
```

`alt` is what a screen reader announces and what Google reads — describe what is
actually in the picture. `caption` is optional and shows over the image.

Three to six photographs is the sweet spot. More than eight and nobody scrolls.

**Field team tip:** photograph the shopfront with the signage visible, in
landscape, in daylight. That single shot does more work than five interior
photos, because it lets a buyer recognise the place when they arrive.

---

## 3. Selling and placing an advertisement

There are **13 ad slots**. Every one that has no live advertisement
automatically shows "Advertisement slot available" with your sales email — so
unsold inventory advertises itself.

### The slots

| Key | Where | Artwork |
|---|---|---|
| `home-leaderboard` | Top of homepage | 970 × 90 |
| `home-billboard` | Mid homepage | 970 × 250 |
| `home-lower` | Lower homepage | 970 × 90 |
| `directory-strip` | Above directory results | 970 × 90 |
| `directory-sidebar` | Directory sidebar | 300 × 250 |
| `directory-infeed` | Inside the results list | text only |
| `tenders-leaderboard` | Top of tenders board | 970 × 90 |
| `tenders-infeed` | Inside tender list | text only |
| `tenders-sidebar` / `tenders-sidebar-b` | Tenders sidebar | 300 × 250 |
| `jobs-leaderboard` | Top of jobs board | 970 × 90 |
| `jobs-sidebar` | Jobs sidebar | 300 × 250 |
| `news-sidebar` | News sidebar | 300 × 250 |
| `footer-leaderboard` | Site-wide footer | 728 × 90 |

### Placing an image advertisement

Upload the creative to `images/ads/` (PNG or JPG, under 150 KB), then add an
entry to the `ads` array in `data/ads.json`:

```json
{
  "id": "crownpaints-2026-q4",
  "slot": "home-leaderboard",
  "active": true,
  "start": "2026-10-01",
  "end": "2026-12-31",
  "advertiser": "Crown Paints Uganda",
  "image": "images/ads/crownpaints-970x90.png",
  "alt": "Crown Paints Uganda — trade discounts for contractors",
  "link": "https://crownpaints.co.ug"
}
```

The `start` and `end` dates matter: **the advertisement appears and disappears
on its own.** You do not have to remember to pull a campaign the day it expires,
and you cannot accidentally run someone's advert for free for three months.

To pause a campaign without deleting it, set `"active": false`.

### Placing a flier

A flier keeps its **natural shape** — portrait A4, square, anything. It is never
cropped or stretched, and it gets an "Enlarge" link that opens the full file.
Good for a supplier who already has a printed promo sheet and no web banner.

```json
{
  "id": "hardware-promo-oct",
  "slot": "directory-sidebar",
  "advertiser": "Kisenyi Hardware",
  "flier": "images/ads/kisenyi-promo.png",
  "alt": "Kisenyi Hardware October cement promotion",
  "link": "https://wa.me/256772000000",
  "active": true, "start": "2026-10-01", "end": "2026-10-31"
}
```

Aim for **800–1200px on the long edge**, under 300KB. Note the link can be a
`wa.me` WhatsApp link — for most Ugandan advertisers that converts better than a
website they do not have.

### Placing a video advertisement

```json
{
  "id": "cement-tvc-q4",
  "slot": "home-billboard",
  "advertiser": "Sample Cement Ltd",
  "video": "images/ads/cement.mp4",
  "poster": "images/ads/cement-poster.jpg",
  "alt": "Cement delivery service advertisement",
  "link": "https://example.com",
  "active": true, "start": "2026-10-01", "end": "2026-12-31"
}
```

| Requirement | Value |
|---|---|
| Format | MP4, H.264 video, AAC audio |
| Resolution | 1280×720 is plenty; 1920×1080 maximum |
| Length | Under 30 seconds |
| File size | **Under 5MB.** This is the one that matters — your viewers are on mobile data |
| Poster | Same aspect ratio as the video, JPG, under 150KB |

Video plays **muted with controls**, never autoplaying with sound. Clicking it
opens the advertiser's link like any other creative.

### Placing a text advertisement

Text advertisements need no artwork, which makes them by far the easiest thing
to sell to your first advertisers — a hardware supplier who has no design team
can still buy one over WhatsApp.

```json
{
  "id": "centenary-2026-q4",
  "slot": "directory-infeed",
  "active": true,
  "start": "2026-10-01",
  "end": "2026-12-31",
  "advertiser": "Centenary Bank",
  "title": "Business loans for construction firms",
  "body": "Flexible overdraft and term facilities. Fast approval.",
  "cta": "Find out more",
  "link": "https://centenarybank.co.ug"
}
```

## Monthly spotlight artwork

Two slots on the homepage, in `images/spotlight/`.

| Slot | Shape | Size | Notes |
|---|---|---|---|
| Product of the Month | 4:3 | 1200 × 900 | The advertiser's own product photograph. Plain background works best. |
| Benchmark Project | 16:9 | 1600 × 900 | A real site or building photograph. **Get permission and credit the photographer.** |

Both under 300KB. Edit the entries under **Monthly slots** in the admin dashboard.

**The two slots follow different rules, and the difference matters.** Product of
the Month is sold and is labelled as advertising wherever it appears. Benchmark
Project is editorial, chosen on merit, and is never for sale. The admin editor
enforces this — the project form has no advertiser or link field at all, and
`sponsored` is forced to false on save.

Keep that line. The moment the project slot can be bought, readers stop trusting
it, and you have lost the thing that makes anyone read the homepage twice.

### Checking a creative before it goes live

Open the admin dashboard and go to **Media check**. It loads every image and
video the site references, reads its real pixel dimensions, and compares them
against the slot. It tells you whether a file will letterbox, whether it is too
small and will look soft, and whether it is so large that mobile visitors are
paying for pixels they never see.

It also flags any advertisement with **no click-through link** — an advertiser
paying for clicks they cannot receive.

### Why nothing is ever distorted

Slots set a maximum box. Creatives use `object-fit: contain` and keep their own
aspect ratio inside it. If the shapes do not match, the creative letterboxes with
space around it rather than being squashed.

That is a deliberate trade: wasted space is a conversation with the advertiser
about sending a better file. A stretched logo is a brand problem you will hear
about, and they will not renew.

Firm photographs are the one exception — thumbnails crop to keep the grid even,
but clicking one opens the full uncropped image at its true proportions, with its
pixel dimensions shown.

### What is tracked

Every slot fires an `ad_impression` event, and every click fires `ad_click` with
the slot and advertisement id. Once GA4 is installed, that is your proof of
delivery — and the thing an advertiser will ask for before they renew.

All advertiser links carry `rel="nofollow sponsored"`, which is what Google
requires for paid links. Without it you risk a manual penalty on the whole site.

---

## 4. Editing everything else

| To change | Edit |
|---|---|
| A firm's details, tier, rating | `data/firms.json` |
| Categories, districts, accreditations | `data/taxonomy.json` |
| Tenders | `data/tenders.json` |
| Jobs | `data/jobs.json` |
| News articles | `data/articles.json` |
| Material prices | `data/prices.json` |
| Advertisements | `data/ads.json` |
| Company name, email, phone, headline figures | the `SITE` object in `index.html` |
| Page wording, headings, marketing copy | `index.html` |

### Editing JSON safely

1. Open the file on GitHub, click the **pencil** icon.
2. Make the change. Keep every comma, bracket and quote exactly as they are.
3. Scroll down, write what you changed, click **Commit changes**.

**Before committing, paste the whole file into [jsonlint.com](https://jsonlint.com)
and press Validate.** One missing comma stops the entire site from loading. It
takes ten seconds and it will save you eventually.

If you do break it, GitHub keeps every version: open the file → **History** →
pick the last good version → **Revert**. Nothing is ever lost.

---

## 5. Before you go live

- [ ] Delete the sample logos, photographs and the sample advertisement
- [ ] Replace the 12 sample firms in `firms.json` with firms you have actually visited
- [ ] Get **written permission** before publishing any firm's logo — a logo is a trademark, and using one without consent is a separate problem from publishing a phone number
- [ ] Compress every image before uploading
- [ ] Check the site on a phone over mobile data, not office wifi

---

## When this stops being enough

Around **200 listings**, or when firms start asking to change their own photos,
editing JSON by hand becomes the bottleneck. That is the signal to build Stage 3
— accounts, real uploads and a firm dashboard.

Not before. Every week you spend building an upload system is a week nobody is
in Kisenyi collecting listings, and the listings are the business.
