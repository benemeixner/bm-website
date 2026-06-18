# benediktmeixner.com

Personal academic site for Dr. Benedikt Meixner, built with
[Hugo Blox](https://hugoblox.com) (Academic CV template) and Hugo.

## How this is structured

This site is a **single long homepage** (Hartmann-style) with anchored
sections, rather than separate pages per topic:

- `content/_index.md` — the whole homepage: Bio, Research (narrative by
  theme), Publications, Teaching, Talks & Outreach, Contact. Each section
  has a `block:` type and (for navigation) an `id:`.
- `config/_default/menus.yaml` — nav links point to `/#research`,
  `/#publications`, etc. — these must match the `id:` values in `_index.md`.
- `content/experience.md` — a separate, optional CV/resume page (education,
  experience, skills) — useful for job applications even if it's not in the
  main single-page flow.
- `content/publications/` — auto-populated from `publications.bib` (see below).
- `content/events/` — talks (used by the "Talks & Outreach" section).
- `bib/publications-manual.bib` — hand-maintained BibTeX for anything without a DOI.
  Add entries here for university-internal reports, book chapters not yet registered, etc.
  These are merged with the auto-synced ORCID entries into `publications.bib` at the root.
  (Note: bib files live in `bib/` not `data/` — Hugo tries to parse everything in `data/`.)
- `data/authors/me.yaml` — your bio, affiliations, interests, links. Feeds
  the homepage biography block.
- `config/_default/params.yaml` — site-wide settings incl. theme color
  (currently `orange`, vs. Hartmann's blue).
- `static/CNAME` — tells GitHub Pages your custom domain is `benediktmeixner.com`.

To add a new homepage section, copy one of the existing `block: markdown`
entries in `content/_index.md`, give it a unique `id:`, and add a matching
menu entry in `menus.yaml` (`url: /#your-id`).

## Publications: how the automation works

1. `.github/workflows/sync-orcid-publications.yml` runs weekly (and can be
   triggered manually from the Actions tab). It runs
   `scripts/sync_orcid_publications.py`, which:
   - fetches your works from ORCID (`0000-0001-7044-9426`)
   - looks up full metadata on Crossref for anything with a DOI
   - writes `data/publications-orcid.bib` (auto-generated)
   - combines it with `data/publications-manual.bib` (hand-maintained) into
     `publications.bib` at the repo root
2. If `publications.bib` changes and gets pushed to `main`, the existing
   `.github/workflows/import-publications.yml` workflow runs `academic import`
   and opens a **pull request** with new/updated pages in `content/publications/`.
3. You review and merge that PR → the site rebuilds and deploys automatically.

**For anything without a DOI** (university-internal reports, etc.), add a
BibTeX entry to `data/publications-manual.bib` — see the example in that file.

**First run:** trigger the sync manually once everything is set up
(Actions tab → "Sync Publications From ORCID" → "Run workflow"), then review
the resulting PR from "Import Publications From Bibtex" before merging.

## Setup checklist (one-time)

1. Push this folder to a new GitHub repo (e.g. `benediktmeixner/benediktmeixner.com`).
2. In the repo: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. In the repo: **Settings → Pages → Custom domain** → enter `benediktmeixner.com`
   (the `static/CNAME` file already contains this, but GitHub also needs it set
   in the Pages settings to provision HTTPS).
4. At your domain registrar, point DNS for `benediktmeixner.com` to GitHub Pages:
   - Four `A` records for `@` pointing to:
     `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - (Optional) a `CNAME` record for `www` pointing to `<your-github-username>.github.io`
   - See [GitHub's docs](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)
     for the current details.
5. Push to `main` — the `Deploy website to GitHub Pages` workflow builds and
   publishes the site.

## TODOs before going live

Search for `# TODO` in `data/authors/me.yaml` for things worth filling in:
- Education history (degree, institution, dates)
- Experience start dates (currently placeholders)
- Google Scholar link, LinkedIn (optional)
- A profile photo: replace `assets/media/authors/me.png`

## Local preview

```bash
npm install
npx hugo server --disableFastRender
```

Then open the printed `localhost` URL. (Requires Hugo extended ≥ 0.161 —
see `hugoblox.yaml` for the pinned version used in CI.)
