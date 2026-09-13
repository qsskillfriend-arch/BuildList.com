/**
 * ═══════════════════════════════════════════════════════════════
 * BUILDLIST.COM — LISTING COLLECTION FORM
 * A product of Sharplink Ventures (U) Limited
 *
 * Builds the whole Google Form for you. You do not type any of it.
 *
 * HOW TO RUN (5 minutes, no software to install):
 *   1. Go to script.google.com  →  New project
 *   2. Delete whatever is in the editor
 *   3. Paste this entire file
 *   4. Rename the project "BuildList.com form" (top left)
 *   5. Press Run (▶). Choose buildListingForm if asked.
 *   6. Google asks for permission the first time:
 *        "Google hasn't verified this app" → Advanced →
 *        "Go to BuildList.com form (unsafe)" → Allow
 *      That warning is normal for your own scripts. You are granting
 *      permission to yourself, not to a third party.
 *   7. View → Logs. The edit link and public link are printed there.
 *
 * TO CHANGE ANYTHING later: edit the CONFIG block, delete the old
 * form from your Drive, and run it again.
 * ═══════════════════════════════════════════════════════════════
 */

const CONFIG = {
  title: 'Add your business to BuildList.com — free',
  formFileName: 'BuildList.com — Listing Collection',
  sheetName: 'BuildList.com — Listing Responses',
  contactEmail: 'hello@buildlist.com',
  whatsapp: '+256 700 000 000',

  // Must match data/taxonomy.json exactly, or listings land in the wrong filter
  categories: [
    'Architecture & Design',
    'Quantity Surveying',
    'Civil & Structural Engineering',
    'Land Surveying',
    'Property Valuers',
    'Urban & Town Planning',
    'General Contracting',
    'Electrical Contracting',
    'Plumbing & Fire Fighting',
    'Heating, Ventilation & Air Conditioning',
    'Structural Steel Design',
    'Landscaping & External Works',
    'Building Management Systems',
    'ICT & Network Infrastructure',
    'Facility Management',
    'Health & Safety Consulting',
    'Environmental & Sustainability',
    'Real Estate Development',
    'Other — tell us below'
  ],

  districts: ['Kampala','Wakiso','Mukono','Jinja','Entebbe','Mbarara','Gulu','Hoima',
              'Kayunga','Kabale','Tororo','Luweero','Bushenyi','Busia','Mbale','Other'],

  accreditations: ['ARB Registered','UIPE Member','ISU Member','ERB Registered',
                   'ISO Certified','PPDA Listed','None of these']
};

function buildListingForm() {
  const form = FormApp.create(CONFIG.formFileName);

  form.setTitle(CONFIG.title)
      .setDescription(
        'BuildList.com is Uganda\'s construction industry directory — architects, engineers, ' +
        'quantity surveyors, contractors and suppliers, all in one place.\n\n' +
        'A basic listing is FREE and stays free. It takes about 3 minutes.\n\n' +
        'What you get: your own page with your phone number and a WhatsApp button, so people ' +
        'searching for what you do can reach you in one tap.\n\n' +
        'Questions? WhatsApp ' + CONFIG.whatsapp + ' or email ' + CONFIG.contactEmail)
      .setCollectEmail(false)
      .setAllowResponseEdits(true)
      .setLimitOneResponsePerUser(false)
      .setProgressBar(true)
      .setShowLinkToRespondAgain(true)
      .setConfirmationMessage(
        'Thank you — we have your details.\n\n' +
        'We call every business before publishing, to check the number works. ' +
        'Expect a call within 3 working days from ' + CONFIG.whatsapp + '.\n\n' +
        'Once live you will get a link to your page that you can share on WhatsApp.');

  /* ── SECTION 1: the business ──────────────────────────────── */
  form.addSectionHeaderItem()
      .setTitle('About your business')
      .setHelpText('Just the basics. Nothing here is published until we have spoken to you.');

  form.addTextItem()
      .setTitle('Business name')
      .setHelpText('Exactly as it appears on your signage or letterhead.')
      .setRequired(true);

  form.addListItem()
      .setTitle('What does your business do?')
      .setHelpText('Choose the closest match. You can add more below.')
      .setChoiceValues(CONFIG.categories)
      .setRequired(true);

  form.addCheckboxItem()
      .setTitle('Any other categories you work in?')
      .setHelpText('Optional. Only tick what you genuinely do — a wrong category means the wrong enquiries.')
      .setChoiceValues(CONFIG.categories.slice(0, -1))
      .setRequired(false);

  form.addParagraphTextItem()
      .setTitle('In one or two sentences, what do you actually supply or do?')
      .setHelpText('Plain language, as you would explain it to a customer. ' +
                   'Example: "We supply and fix roofing sheets, trusses and accessories. ' +
                   'Free delivery within Kampala on orders above 2 million."')
      .setRequired(true);

  form.addTextItem()
      .setTitle('Main services or products')
      .setHelpText('Separate with commas. Example: cement, aggregate, steel bars, roofing sheets')
      .setRequired(false);

  /* ── SECTION 2: where ─────────────────────────────────────── */
  form.addPageBreakItem()
      .setTitle('Where you are')
      .setHelpText('So customers nearby can find you.');

  form.addListItem()
      .setTitle('District')
      .setChoiceValues(CONFIG.districts)
      .setRequired(true);

  form.addTextItem()
      .setTitle('Area, trading centre or street')
      .setHelpText('Example: Kisenyi, or Ntinda Trading Centre, or Plot 12 Kampala Road')
      .setRequired(true);

  form.addTextItem()
      .setTitle('Nearest landmark')
      .setHelpText('Optional, but it genuinely helps customers find you. ' +
                   'Example: opposite Shell, or next to Nakawa Market gate')
      .setRequired(false);

  /* ── SECTION 3: contact ───────────────────────────────────── */
  form.addPageBreakItem()
      .setTitle('How customers reach you')
      .setHelpText('This is the part that earns you business. Please make sure the number is right.');

  const phone = form.addTextItem()
      .setTitle('Phone number')
      .setHelpText('Include the country code: +256...')
      .setRequired(true);
  phone.setValidation(
    FormApp.createTextValidation()
      .requireTextMatchesPattern('^[\\+0][0-9\\s\\-]{8,15}$')
      .setHelpText('Enter a valid Ugandan number, for example +256772123456')
      .build());

  form.addTextItem()
      .setTitle('WhatsApp number')
      .setHelpText('Leave blank if it is the same as above. Most enquiries come through WhatsApp.')
      .setRequired(false);

  const email = form.addTextItem()
      .setTitle('Email address')
      .setHelpText('Optional.')
      .setRequired(false);
  email.setValidation(
    FormApp.createTextValidation().requireTextIsEmail()
      .setHelpText('That does not look like an email address').build());

  form.addTextItem()
      .setTitle('Website or Facebook page')
      .setHelpText('Optional. Paste the full link.')
      .setRequired(false);

  form.addTextItem()
      .setTitle('Your name')
      .setHelpText('Who we should ask for when we call.')
      .setRequired(true);

  form.addTextItem()
      .setTitle('Your role in the business')
      .setHelpText('Owner, manager, sales — whatever fits.')
      .setRequired(false);

  /* ── SECTION 4: credibility ───────────────────────────────── */
  form.addPageBreakItem()
      .setTitle('A few optional details')
      .setHelpText('These make your listing stand out. Skip anything that does not apply.');

  form.addTextItem()
      .setTitle('Year the business started')
      .setRequired(false);

  form.addMultipleChoiceItem()
      .setTitle('How many people work there?')
      .setChoiceValues(['Just me','2–5','6–10','11–20','21–50','51–100','More than 100'])
      .setRequired(false);

  form.addCheckboxItem()
      .setTitle('Are you registered with any of these?')
      .setHelpText('We check these against the public registers before adding a verified badge. ' +
                   'Only tick what you are actually registered with.')
      .setChoiceValues(CONFIG.accreditations)
      .setRequired(false);

  form.addTextItem()
      .setTitle('Registration or membership number')
      .setHelpText('Optional. Speeds up verification.')
      .setRequired(false);

  form.addMultipleChoiceItem()
      .setTitle('Do you have a logo you can send us?')
      .setHelpText('WhatsApp it to ' + CONFIG.whatsapp + ' with your business name. ' +
                   'A listing with a logo gets noticeably more clicks.')
      .setChoiceValues(['Yes, I will WhatsApp it','No logo yet','I would like help making one'])
      .setRequired(false);

  form.addMultipleChoiceItem()
      .setTitle('Photographs of your shop, workshop or work?')
      .setHelpText('Send them to the same WhatsApp number. A photograph of your shopfront ' +
                   'tells a customer you are real — it is the single biggest thing that gets you called.')
      .setChoiceValues(['Yes, I will send photos','No photos right now',
                        'Please send someone to photograph it'])
      .setRequired(false);

  /* ── SECTION 5: consent ───────────────────────────────────── */
  form.addPageBreakItem()
      .setTitle('Permission to publish')
      .setHelpText('Required by Uganda\'s Data Protection and Privacy Act, 2019. ' +
                   'Plain terms, no small print.');

  form.addMultipleChoiceItem()
      .setTitle('Do you give BuildList.com permission to publish the details above?')
      .setHelpText('We publish your business name, category, area and contact details so customers ' +
                   'can find you. You can ask us to remove your listing at any time and we will do ' +
                   'it within 48 hours. We do not sell your details to anyone.')
      .setChoiceValues(['Yes, publish my business',
                        'No — I only want to hear more first'])
      .setRequired(true);

  form.addMultipleChoiceItem()
      .setTitle('Can we call you to confirm the details before publishing?')
      .setHelpText('We call every business. It is how we keep dead numbers off the directory.')
      .setChoiceValues(['Yes','Prefer WhatsApp message','Prefer email'])
      .setRequired(true);

  form.addMultipleChoiceItem()
      .setTitle('May we send you our weekly digest?')
      .setHelpText('New tenders, material prices and industry news. One message a week. ' +
                   'Unsubscribe any time.')
      .setChoiceValues(['Yes please','No thanks'])
      .setRequired(false);

  /* ── Extra digest recipients ────────────────────────────────
     A business usually wants more than one person seeing tender
     notices — the owner, the estimator, the site manager. Three
     slots covers almost everyone without turning the form into
     a chore.

     The confirmation question below is not decoration. Adding
     somebody else's address to a mailing list without their
     knowledge is exactly what the Data Protection and Privacy Act,
     2019 is about. We ask, we record the answer, and every nominated
     address gets a single confirm-or-ignore message before it ever
     receives a digest. */
  form.addSectionHeaderItem()
      .setTitle('Colleagues who should also get the digest')
      .setHelpText('Optional. Add up to three colleagues — an estimator, a site manager, ' +
                   'a director — who should receive the weekly tenders and price digest.\n\n' +
                   'We send each of them one message asking if they want it. Nobody is added ' +
                   'to a list without saying yes.');

  for (var n = 1; n <= 3; n++) {
    var extra = form.addTextItem()
        .setTitle('Colleague ' + n + ' — email address')
        .setHelpText(n === 1
          ? 'Optional. Leave blank if it is just you.'
          : 'Optional.')
        .setRequired(false);
    extra.setValidation(
      FormApp.createTextValidation().requireTextIsEmail()
        .setHelpText('That does not look like an email address').build());

    form.addTextItem()
        .setTitle('Colleague ' + n + ' — name and role')
        .setHelpText('Optional. Example: Grace Nakato, Estimator')
        .setRequired(false);
  }

  form.addMultipleChoiceItem()
      .setTitle('Do these colleagues know you are giving us their email?')
      .setHelpText('We ask because Uganda\'s Data Protection and Privacy Act, 2019 applies to ' +
                   'their details as much as yours. Either answer is fine — it only changes the ' +
                   'wording of the first message we send them.')
      .setChoiceValues(['Yes, they know and expect it',
                        'Not yet — please introduce yourselves',
                        'Not applicable, I did not add anyone'])
      .setRequired(false);

  form.addParagraphTextItem()
      .setTitle('Anything else we should know?')
      .setRequired(false);

  form.addTextItem()
      .setTitle('Who told you about BuildList.com?')
      .setHelpText('Optional — helps us know which of our agents and referrals are working. ' +
                   'A name, a WhatsApp group, or where you saw the sticker.')
      .setRequired(false);

  /* ── Responses land in a spreadsheet ──────────────────────── */
  const ss = SpreadsheetApp.create(CONFIG.sheetName);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  /* ── Print the links ──────────────────────────────────────── */
  const out = [
    '',
    '══════════════════════════════════════════════════════',
    ' BUILDLIST LISTING FORM — CREATED',
    '══════════════════════════════════════════════════════',
    '',
    ' SHARE THIS LINK (send to businesses):',
    '   ' + form.getPublishedUrl(),
    '',
    ' SHORT LINK (easier on a sticker or over the phone):',
    '   ' + form.shortenFormUrl(form.getPublishedUrl()),
    '',
    ' EDIT THE FORM:',
    '   ' + form.getEditUrl(),
    '',
    ' RESPONSES SPREADSHEET:',
    '   ' + ss.getUrl(),
    '',
    '══════════════════════════════════════════════════════',
    ' NEXT: make a QR code of the short link at qr-code-generator.com',
    ' and put it on your field team\'s flyers and window stickers.',
    '══════════════════════════════════════════════════════'
  ].join('\n');

  Logger.log(out);
  return out;
}

/**
 * Optional extra: emails you a daily summary of new submissions so
 * nobody has to remember to check the spreadsheet.
 *
 * To switch on: Triggers (clock icon) → Add trigger →
 *   function: dailySubmissionDigest, source: Time-driven,
 *   type: Day timer, time: 7am–8am
 */
function dailySubmissionDigest() {
  const ss = SpreadsheetApp.openById('PASTE_YOUR_SPREADSHEET_ID_HERE');
  const sheet = ss.getSheets()[0];
  const data = sheet.getDataRange().getValues();
  if (data.length < 2) return;

  const header = data[0];
  const tsCol = 0;
  const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000);
  const fresh = data.slice(1).filter(r => new Date(r[tsCol]) > cutoff);
  if (!fresh.length) return;

  const nameCol = header.indexOf('Business name');
  const catCol  = header.indexOf('What does your business do?');
  const phCol   = header.indexOf('Phone number');

  const body = fresh.map(r =>
    '• ' + r[nameCol] + '  —  ' + r[catCol] + '  —  ' + r[phCol]).join('\n');

  MailApp.sendEmail({
    to: CONFIG.contactEmail,
    subject: fresh.length + ' new BuildList.com listing' + (fresh.length > 1 ? 's' : '') + ' to verify',
    body: 'New submissions in the last 24 hours:\n\n' + body +
          '\n\nCall each one to confirm the number works, then add them in the admin dashboard.\n\n' +
          ss.getUrl()
  });
}
