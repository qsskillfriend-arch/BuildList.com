# Data files

Everything the site displays lives in this folder. You can edit these files
through GitHub's web interface — it validates the JSON, keeps full history,
and lets you revert a bad edit. That is a real admin panel for the first
couple of hundred listings. Do not build a CMS yet.

---

## Where this data came from

`firms.json` holds **618 real listings** imported from `BuildList.com_All_Listings.xlsx`.

Every firm carries a `descSource` field recording where its description came from:

| Value | Count | Meaning |
|---|---|---|
| `researched` | 2 | Written from the firm's own website or a reputable directory. Specific and evidenced. |
| `sheet` | 210 | Recovered from the per-category tabs of your spreadsheet, which the master tab had lost. |
| `derived` | 406 | Written from the firm's own category and location. True by construction, but adds nothing your spreadsheet did not already contain. |

The 406 derived ones read like *"Electrical installation and contracting firm based in Ntinda, Kampala."*
That is accurate and useful in search results, but it is not research. Filter the
admin by `descSource` when you want to work through them.

**Nothing was invented.** No founding years, staff counts, project lists, client
names or certifications were written unless a source said so.

Two other fields are deliberately conservative:

- **`verified` is `false` on all 618.** The spreadsheet's Tier column marked 30 as
  "Verified", but that is an editorial designation with no date or evidence behind
  it. Your site tells visitors a verified badge means you confirmed the phone number
  and premises yourself. Set it true as your field team actually does that; the
  original value is kept in `sourceTier`.
- **`tier` is `free` on all 618.** Paid tiers mean somebody paid. Promote them in the
  admin when money clears.

Ratings are `0` with `0` reviews, and the site shows "No reviews yet" rather than
empty stars.

---

## ⚠️ Read this before you go live

**These are real Ugandan businesses, published without their consent so far.**

Publishing a real business's name, phone number and address without their
consent is a problem on three counts:

1. **Data protection.** Uganda's Data Protection and Privacy Act, 2019 covers
   the personal contact details of business owners. Your own About page now
   commits to recording consent for every listing.
2. **Accuracy.** A wrong number or a closed shop attributed to a named firm is
   the fastest way to get a complaint, and the firm has every right to make one.
3. **Your own claims.** The site says listings are verified and that you confirm
   the phone number and premises yourself. Sample data makes that untrue on
   day one.

Before launch you need a consent and takedown process running: a clear "remove my
listing" route honoured within 48 hours, and a record of which firms your agents
have actually spoken to. Publishing a business's phone number is normal directory
practice, but the Data Protection and Privacy Act, 2019 gives them a right to be
removed, and your own About page promises it.

---

## Files

| File | Contains |
|---|---|
| `taxonomy.json` | Categories, districts, accreditations, tiers. Add a category here and it appears in every filter and dropdown automatically. |
| `firms.json` | Firm listings. One object per firm. |
| `tenders.json` | Procurement notices. Closed notices hide themselves — see below. |
| `jobs.json` | Vacancies. Also expire automatically. |
| `articles.json` | News and guide articles. |
| `prices.json` | Material price index plus the date it was collected. |
| `events.json` | Industry events — expos, CPD, association meetings. Self-expiring like tenders. |
| `spotlight.json` | Product of the Month (paid) and Benchmark Project (editorial), plus their archives. |

---

## Adding a firm

```json
{
  "id": 13,
  "slug": "kisenyi-hardware-stores",
  "name": "Kisenyi Hardware Stores",
  "initials": "KH",
  "categories": ["material-suppliers"],
  "district": "kampala",
  "area": "Kisenyi, Kampala",
  "desc": "General building materials — cement, aggregate, steel, roofing.",
  "rating": 4.3,
  "reviews": 12,
  "tier": "starter",
  "accreditations": [],
  "services": ["Cement", "Aggregate", "Steel", "Roofing sheets"],
  "established": 2017,
  "employees": "5-10",
  "phone": "+256772000000",
  "whatsapp": "+256772000000",
  "email": "",
  "website": "",
  "verified": true,
  "verifiedDate": "2026-09-10",
  "createdAt": "2026-09-10",
  "projects": []
}
```

Rules that matter:

- **`slug` must be unique and must never change.** It is the firm's permanent
  URL (`#/firms/kisenyi-hardware-stores`). Changing it breaks every link the
  firm has shared, including their own WhatsApp status.
- **`categories` and `district` must use slugs from `taxonomy.json`**, not
  display names. A typo means the firm silently disappears from that filter.
- **`tier`** must be one of `platinum`, `premium`, `verified`, `starter`, `free`.
  This controls both the badge and the default sort order — paid tiers rank first.
- **`verifiedDate`** is shown on the listing as "Verified Aug 2026". Leave
  `verified: false` and `verifiedDate: null` for firms you have not checked.
  A visible honest gap is better than an unearned badge.
- **`whatsapp`** should be in full international format. The tap-to-chat link
  strips everything except digits.

If a firm asks to be removed, delete its object and commit. Action this within
48 hours — that is what the privacy policy promises.

---

## Tenders and jobs expire by themselves

You do not need to delete closed notices. Anything whose `deadline` (tenders)
or `closesAt` (jobs) has passed is hidden automatically, and tenders closing
within 14 days are flagged "Closing Soon" on their own.

You still need to **add** new ones daily. A tender board that has not moved in
three weeks tells a procurement officer the site is abandoned, and they do not
come back.

---

## Prices

`prices.json` carries an `updated` date and a `sources` list. Both are shown on
the site. Update it weekly from the same three named suppliers so the series is
comparable over time — after twelve months that history becomes a product you
can sell, and nobody else in Uganda has it.

A stale price index is worse than no price index, because people quote from it.
