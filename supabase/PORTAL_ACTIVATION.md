# BuildList portal activation — images, videos and current backend endpoints

This version wires the existing staff portal to the Supabase backend already present in this project.

## What is active

- Supabase email/password login, magic link and password reset
- Staff roles: admin, editor and agent
- Firm records and approval workflow
- Firm child records: categories, accreditations, services, photos and projects
- Articles
- Tenders and jobs data loading
- Material price snapshots
- Advertising inventory
- Monthly spotlight records
- Media library records
- Image uploads with browser-side responsive variants
- Firm logo attachment from the portal
- Firm photo attachment from the portal
- Firm video upload and attachment from the portal
- Resumable video uploads through Supabase Storage/TUS
- Public profile video output through `video` / `videoPoster` in `data/firms.json`
- Public static build remains independent of live Supabase availability

## Supabase setup

1. Open **Supabase → SQL Editor**.
2. Run the complete `supabase/schema.sql`. It is written to be safe to re-run and adds the media/video/spotlight structures to an existing database.
3. Run `supabase/seed.sql`.
4. Create your staff user under **Authentication → Users**.
5. Add the user's UUID to `staff` with role `admin`, `editor` or `agent`.
6. Put the **Project URL** and **anon key** into the two constants at the top of `portal.html`. Never put the `service_role`/secret key in the browser.

## Media rules

### Images

The portal accepts image files up to 25 MB at source level and creates responsive variants in the browser.

- `logo` → public logo storage + updates the selected firm's `logo_url`
- `firm-photo` → public firm-photo storage + creates a `firm_photos` row
- `article`, `flier`, `ad-*`, `spotlight` → media library storage

### Videos

Select **Video**, choose **Firm video**, select a firm, then upload. The portal uses a resumable upload flow and generates a poster frame where the browser supports it. The uploaded video is added to `firm_videos`; the public build displays the first ordered firm video.

The portal deliberately caps video files at **45 MB** because Supabase Free currently has a 50 MB global file-size limit. Larger video hosting should be moved to a dedicated video service or a paid storage plan rather than bypassing the limit.

## Current backend services/endpoints

The project does not use custom `/api/*` endpoints. Its backend surface is Supabase:

- Auth: Supabase Auth
- Data: Supabase PostgREST tables
- Files: Supabase Storage
- Build synchronization: `supabase/pull.js`
- Database migration: `supabase/migrate.js`
- Static page generation: `build.js`

The public site continues to use generated JSON/static pages. The portal is the editing interface and Supabase is the source of truth after migration.

## Netlify

Set these environment variables for deploy-time synchronization:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

The Netlify build command is already configured as:

```text
node supabase/pull.js && node build.js
```

If Supabase is unavailable, `pull.js` deliberately keeps the last committed JSON data so the public site can still deploy.
