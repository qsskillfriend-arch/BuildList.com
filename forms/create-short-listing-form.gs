/**
 * ═══════════════════════════════════════════════════════════════
 * BUILDLIST.COM — SHORT LISTING FORM
 * A product of Sharplink Ventures (U) Limited
 *
 * The same eight questions as the printed form, so a submission from
 * either route produces the same record. Deliberately short: every
 * extra question costs you completions, and anything else can be
 * asked on the verification call.
 *
 * HOW TO RUN (about 5 minutes, nothing to install):
 *   1. script.google.com  →  New project
 *   2. Delete what is in the editor, paste this whole file
 *   3. Rename it "BuildList short form" (top left)
 *   4. Press Run (▶)
 *   5. Google warns "hasn't verified this app" → Advanced →
 *      "Go to … (unsafe)" → Allow. That is normal for your own script.
 *   6. View → Logs. Your share link, short link and responses
 *      spreadsheet are printed there.
 *
 * Changing anything: edit CONFIG, delete the old form from Drive,
 * run it again. The categories must match data/taxonomy.json or
 * submissions land in the wrong filter.
 * ═══════════════════════════════════════════════════════════════
 */

const CONFIG = {
  formFileName: 'BuildList — Add your business (short)',
  sheetName:    'BuildList — Short form responses',
  whatsapp:     '+256 700 000 000',
  email:        'hello@buildlist.com',

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
    'Tradesmen (individual or small crew)'
  ],

  districts: ['Kampala','Wakiso','Mukono','Jinja','Entebbe','Mbarara','Gulu','Hoima',
              'Kayunga','Kabale','Tororo','Luweero','Bushenyi','Busia','Mbale','Other']
};

function buildShortForm() {
  const form = FormApp.create(CONFIG.formFileName);

  form.setTitle('Add your business to BuildList.com — free')
      .setDescription(
        'Eight questions, about three minutes.\n\n' +
        'A basic listing is free and stays free. You get your own page with your ' +
        'phone number and a WhatsApp button, so people searching for what you do can ' +
        'reach you in one tap.\n\n' +
        'Questions? WhatsApp ' + CONFIG.whatsapp)
      .setCollectEmail(false)
      .setProgressBar(false)          // it is one page; a progress bar just adds noise
      .setAllowResponseEdits(true)
      .setShowLinkToRespondAgain(true)
      .setConfirmationMessage(
        'Thank you — we have your details.\n\n' +
        'We telephone every business before publishing, to check the number works. ' +
        'Expect a call within 3 working days from ' + CONFIG.whatsapp + '.\n\n' +
        'Once you are live we send you a link to your page that you can share on WhatsApp.');

  // 1
  form.addTextItem()
      .setTitle('Business name')
      .setHelpText('As it appears on your signage.')
      .setRequired(true);

  // 2
  form.addCheckboxItem()
      .setTitle('What do you do?')
      .setHelpText('Tick one or two. A wrong category means the wrong enquiries.')
      .setChoiceValues(CONFIG.categories)
      .setRequired(true);

  // 3
  form.addParagraphTextItem()
      .setTitle('In one sentence, what do you sell or do?')
      .setHelpText('Plain words, as you would tell a customer. ' +
                   'Example: "We supply and fix roofing sheets, trusses and accessories. ' +
                   'Free delivery in Kampala on orders above 2 million."')
      .setRequired(true);

  // 4
  form.addListItem()
      .setTitle('District')
      .setChoiceValues(CONFIG.districts)
      .setRequired(true);

  // 5
  form.addTextItem()
      .setTitle('Area or trading centre')
      .setHelpText('e.g. Kisenyi. Add the nearest landmark if you have no street address — ' +
                   '"opposite Shell" genuinely helps customers find you.')
      .setRequired(true);

  // 6
  const phone = form.addTextItem()
      .setTitle('Phone number')
      .setHelpText('The one that is always on. Include the country code: +256…')
      .setRequired(true);
  phone.setValidation(
    FormApp.createTextValidation()
      .requireTextMatchesPattern('^[\\+0][0-9\\s\\-]{8,15}$')
      .setHelpText('Enter a valid Ugandan number, for example +256772123456')
      .build());

  // 7
  form.addTextItem()
      .setTitle('WhatsApp number')
      .setHelpText('Leave blank if it is the same as above. Most enquiries arrive this way.')
      .setRequired(false);

  // 8
  form.addTextItem()
      .setTitle('Your name and role')
      .setHelpText('Who we should ask for when we call.')
      .setRequired(true);

  // Optional extras — kept to two, both genuinely useful, neither required
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

  // Consent — required, and the reason this form exists in this shape
  form.addMultipleChoiceItem()
      .setTitle('Do you give BuildList.com permission to publish the details above?')
      .setHelpText('We publish your business name, what you do, your area and your contact ' +
                   'number so customers can find you. You can ask us to remove your listing at ' +
                   'any time and we do it within 48 hours. We do not sell your details to anyone. ' +
                   'Required under the Data Protection and Privacy Act, 2019.')
      .setChoiceValues(['Yes, publish my business', 'No — tell me more first'])
      .setRequired(true);

  form.addTextItem()
      .setTitle('Who told you about BuildList?')
      .setHelpText('Optional — an agent\u2019s name, a WhatsApp group, or where you saw the sticker. ' +
                   'It tells us which of our efforts are working.')
      .setRequired(false);

  const ss = SpreadsheetApp.create(CONFIG.sheetName);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  Logger.log([
    '',
    '══════════════════════════════════════════════════════',
    ' SHORT LISTING FORM — CREATED',
    '══════════════════════════════════════════════════════',
    '',
    ' SHARE THIS LINK:',
    '   ' + form.getPublishedUrl(),
    '',
    ' SHORT LINK (for a sticker, or reading over the phone):',
    '   ' + form.shortenFormUrl(form.getPublishedUrl()),
    '',
    ' EDIT THE FORM:',
    '   ' + form.getEditUrl(),
    '',
    ' RESPONSES:',
    '   ' + ss.getUrl(),
    '',
    '══════════════════════════════════════════════════════',
    ' NEXT: make a QR code of the short link and put it on',
    ' your field stickers. Then import responses with:',
    '   node forms/import-responses.js responses.csv',
    '══════════════════════════════════════════════════════'
  ].join('\n'));
}
