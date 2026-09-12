# Listing collection form

Two files here, and a five-minute setup.

| File | What it does |
|---|---|
| `create-listing-form.gs` | Builds the entire Google Form for you. You type nothing. |
| `import-responses.js` | Turns the responses spreadsheet into listings for the site. |

---

## 1. Create the form (5 minutes)

1. Go to **script.google.com** → **New project**
2. Delete whatever is in the editor
3. Paste the whole of `create-listing-form.gs`
4. Rename the project "BuildList form" (top left)
5. Press **Run** (▶)
6. Google will warn *"Google hasn't verified this app"* → **Advanced** → **Go to BuildList form (unsafe)** → **Allow**.
   That warning is normal for a script you wrote yourself. You are granting permission to your own account, not to a third party.
7. **View → Logs.** Your links are printed there:
   - the public link to share
   - a short link for stickers and phone calls
   - the edit link
   - the responses spreadsheet

Make a QR code of the short link at qr-code-generator.com and put it on your field stickers and flyers.

### Changing anything

Edit the `CONFIG` block at the top — categories, districts, your WhatsApp number — then delete the old form from Drive and run it again.

**The category list must match `data/taxonomy.json` exactly.** If it drifts, submissions land in the wrong filter or get parked under "General Contracting".

### Daily email digest (optional)

`dailySubmissionDigest()` emails you each morning with the new submissions, so nobody has to remember to check the spreadsheet.

1. Copy the spreadsheet ID from its URL into the function
2. Triggers (clock icon) → **Add trigger** → function `dailySubmissionDigest`, time-driven, day timer, 7–8am

---

## 2. Import the responses

In the responses spreadsheet: **File → Download → Comma-separated values**. Then:

```bash
node forms/import-responses.js ~/Downloads/responses.csv
```

It writes `forms/new-listings.json` and prints a summary.

### Digest recipients

The form lets a business nominate **up to three colleagues** — an estimator, a site
manager, a director — to also receive the weekly tenders and price digest. Most
firms want more than one person seeing tender notices, and the person filling in
the form is rarely the person who prices the work.

The importer writes two extra files:

| File | Use |
|---|---|
| `digest-recipients.json` | Full detail with who nominated whom |
| `digest-recipients.csv` | Import straight into Brevo, MailerLite or Mailchimp |

Each recipient is marked either:

- **`opted-in`** — the business's own address, they ticked yes themselves. Safe to add.
- **`awaiting-confirmation`** — a nominated colleague. **Send one confirm-or-ignore
  message before adding them to anything.**

That distinction is not bureaucracy. Adding somebody to a mailing list because a
third party gave you their address is exactly what the Data Protection and Privacy
Act, 2019 covers, and it is also how you get marked as spam. The form asks whether
the colleagues know, and the importer counts how many do not, so you can use
introduction wording for those ones:

> *Moses at Kisenyi Hardware suggested you might want our weekly digest of new
> tenders and material prices. One message a week. Reply YES and we will add you
> — ignore this and we will not write again.*

Duplicates are removed automatically. If two firms nominate the same person, they
get one confirmation, not two.

Colleague addresses that fail validation are flagged with the firm name so you can
ask on the verification call.

### What it refuses to import

| Blocked | Why |
|---|---|
| Anyone who did not tick consent | Publishing them is the thing that gets you a takedown demand and a complaint |
| Submissions with no usable phone number | A listing nobody can call is worse than no listing |
| Duplicates of your existing listings | Matched on both business name and phone number, so you never get two pages for one firm |

It also **flags** rather than silently fixing: categories it cannot map to the taxonomy, and businesses that asked for a photography visit — those are warm leads for a paid listing and it lists them separately with their phone numbers.

### Everything arrives as `pending`

By design. A human telephones before anything appears on the site. That is what the verified badge on your About page actually promises.

Once you have called them, paste the records into `data/firms.json` and set status to `live` in the admin dashboard.

---

## The consent question is the point

The form exists in this shape because of Uganda's Data Protection and Privacy Act, 2019. Consent is a required question with a plain-language explanation and a stated 48-hour removal promise.

Do not remove it, and do not make it optional. It is also the reason the form is a genuine asset: every record that comes through it is consented at the point of entry, unlike the 618 you already hold.
