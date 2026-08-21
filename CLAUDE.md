# CLAUDE.md

This file is read automatically by Claude Code at the start of every session in this repo. Keep it accurate — see "Keeping this file updated" at the bottom.

## What this repo is

Avi Ravishankar's personal site, hosted on GitHub Pages at `avikravi.github.io`. Plain HTML/CSS/JS, no build step, no framework, no npm dependencies for the deployed site itself.

## Files

```
index.html              Home page (bio, experience, skills). As of 2026-08-21, uses the
                         light-editorial design system (see below), not the neon dark one.
projects.html           Project showcase. As of 2026-08-21, uses the light-editorial design
                         system (see below), not the neon dark one.
tracker.html            Live application tracker (reads tracker-data/applications.json)
                         Not linked from the nav bar on purpose — direct-URL-only. Still uses
                         the original neon dark design system — intentionally not converted
                         when index.html/projects.html were redesigned, since its interactive
                         UI (stats grid, status columns, filter chips, resume-tailoring tool)
                         would need separate rework to restyle safely.
                         Also hosts the "Tailor a Resume" tool — see below.
tracker-data/
  applications.json     The tracker's actual data — see schema below
scripts/
  add_application.py    CLI helper to append a new application entry
tailor/
  matching-engine.js    Scores master_resume_data.json entries against a pasted job description
  scoring-engine.js     Computes the 0-100 "Check Match Score" fit score (reuses matching-engine.js)
  doc-builder.js        Builds the resume/cover-letter docx.Document objects from selected entries
  app.js                Wires the tracker.html "Tailor a Resume" form to the three scripts above
master_resume_data.json Source-of-truth for Avi's real resume content (see below)
AvinashResume2026.pdf   The single, canonical resume — linked from the "Download Resume" nav
                         button on all three main pages. As of 2026-08-10, Avi consolidated
                         what used to be two separate resume PDFs (AvinashResume.pdf and
                         Avinash_Resume_2026.pdf, both now deleted) into this one file, which
                         is the ultimate source of truth for both content and formatting.
zgx-nano-case-study.html Working case study on the HP ZGX Nano AI Station (feedback/positive-review
                         scraper boxes, personal research, potential-use-case industry reviews,
                         competitor tracker). Unlisted (meta robots noindex,nofollow, not linked from
                         nav) — direct-URL-only. Originator of the light-editorial design system:
                         as of 2026-08-21, index.html and projects.html were redesigned to match this
                         page's tokens, typography, and flat divided-list layout (see below).
nano.png / nano-header.png  Source and resized product photos used in the case study header.
hp-pmm-worksheet.html    Static reference table itemizing every skill/requirement/responsibility
                         from a specific HP job posting (Principal Technical Product Marketing
                         Manager, AI Solutions) as one row each. No JS, no localStorage, no
                         edit UI — the right-hand "How I Qualify" column is plain HTML that
                         Claude Code updates directly as Avi describes his experience in chat
                         and it's mapped to the matching row(s). Unlisted, styled in HP's
                         actual brand blue (#0096D6) rather than the neon dark tokens below,
                         not linked from nav. Writing style for the "How I Qualify" column:
                         short, complete sentences. Never use a dash (em dash or "--") to
                         join two clauses; split into separate sentences instead.
README.md               Human-facing docs
CLAUDE.md               This file
```

## Design system — DO NOT change without being asked

**Two design systems now coexist in this repo, split by page.** Don't mix their tokens.

### Light-editorial system (`index.html`, `projects.html`, `zgx-nano-case-study.html`)

As of 2026-08-21, `index.html` and `projects.html` were redesigned to match `zgx-nano-case-study.html`'s clean, light, editorial look, at the user's explicit request — all original wording/content was preserved, only the visual system changed. `zgx-nano-case-study.html` remains the source of truth for these tokens:

```css
--bg: #ffffff;
--ink: #191919;
--ink-soft: #3d3d3d;
--ink-faint: #767676;
--line: #e5e5e5;
--blue: #1967b1;
```

Font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`

Shared conventions across these three pages:
- Flat, thin-bordered nav (`border-bottom: 1px solid var(--line)`) — black wordmark logo, uppercase nav links in `--ink-faint`, black underline "active" state, solid black "Download Resume" pill button
- No background animation, no gradients, no glow/blur effects — plain white background throughout
- Page header pattern: optional `.eyebrow` (small uppercase label), bold black `h1`, `.dek` subtitle in `--ink-faint`
- Section pattern: `.panel-title` (bold black `h2`-equivalent) + `.panel-desc` (faint subtitle with a bottom border divider)
- Content is flat divided lists (`.fitem` — `border-top: 1px solid var(--line)` between entries), not boxed/shadowed cards — this is the key visual difference from the dark system below
- Small pill tags (`.tag-co`, `.chip`) for categories/tech stacks: subtle border, no fill or a very light `#fafafa` fill, never a colored gradient

If asked to add a new page or extend `index.html`/`projects.html`, copy tokens and conventions from `zgx-nano-case-study.html` or these two pages — not from `tracker.html`.

### Neon dark system (`tracker.html` only)

`tracker.html` was intentionally left on the original dark neon design when `index.html`/`projects.html` were converted (2026-08-21) — its interactive UI (stats grid, status columns, filter chips, the resume-tailoring tool) would need separate rework to restyle safely, and it's unlinked from nav anyway. Preserve these tokens exactly when editing `tracker.html`:

```css
--neon-pink: #ff006e;
--neon-blue: #00f5ff;
--neon-purple: #8b5cf6;
--hot-pink: #ff0080;
--electric-blue: #0066ff;
--bg-dark: #0a0a0f;
--bg-surface: #1a1a2e;
--text: #ffffff;
--text-dim: #a8b2d1;
```

Font stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', monospace`

Conventions: fixed nav bar with blurred background, gradient logo text ("AR"), uppercase nav links, pink "active" state, gradient "Download Resume" button; animated grid background (`body::before`) + radial gradient overlay (`body::after`); gradient `h2` (pink → blue) section headers; cards with `rgba(26,26,46,0.6)` background, 2px low-opacity-accent border, `border-radius: 16px`, `backdrop-filter: blur(10px)`.

### Nav bar consistency (now split by design system)

The **byte-for-byte-identical nav rule now applies within each design system, not across both**: `index.html` and `projects.html` must keep identical nav markup/CSS (light-editorial system, `index.html` is the source of truth for that pair); `tracker.html` keeps its own nav in the neon dark system, unlinked from the other two — it is no longer expected to match them visually. Nav links on `index.html`/`projects.html` (in order): Home, Projects, Research (external link, `target="_blank" rel="noopener"`, points to `avikravi.github.io/surgical-robotics-tissue-sim/dataset_viewer.html` — a separate repo, not a local page), Download Resume. The only permitted difference between `index.html` and `projects.html` navs is which link carries `class="active"`. If you change one of those two pages' nav, copy the change to the other verbatim. `tracker.html`'s own nav (with its extra "Tracker" link) can be updated independently.

## Tracker data schema (`tracker-data/applications.json`)

Array of objects:

```json
{
  "id": "string, unique, slug-hash format",
  "company": "string",
  "role": "string",
  "dateApplied": "YYYY-MM-DD, or empty string if unknown",
  "status": "applied | interviewing | offer | rejected | ghosted",
  "industry": "free-text tag, used for the filter chips (e.g. tech, academia, consulting, energy, robotics, automotive, finance, healthcare, manufacturing, industrial)",
  "location": "string, optional, currently not rendered in the UI",
  "link": "string, optional, job posting URL",
  "notes": "string, optional — also used to store Avi's personal fit-score ratings like 'Fit score: 85/100'"
}
```

`isExample: true` marks the placeholder seed entry — `scripts/add_application.py` auto-removes it the first time a real entry is added.

Don't invent statuses outside the five listed above — `tracker.html`'s `STATUS_CONFIG` object only knows those five and anything else silently won't render into a column.

## Resume data (`master_resume_data.json`)

Single source of truth for Avi's real work history — every bullet is tagged with its real metric and which industries it's relevant to. This exists so that any future resume-tailoring script never fabricates a metric: it should only ever select and reword from what's in this file.

**Never invent or embellish a metric, title, or date in this file or in any resume generated from it.** The file's own `unresolved_conflicts_for_avi_to_confirm` array currently documents a handful of open conflicts (e.g. team sizes, start dates, metric framing) between different past versions of Avi's resume — check that array before treating any entry it references as fully settled, and add to it rather than silently guessing if you find a new discrepancy.

As of 2026-08-10, `AvinashResume2026.pdf` (repo root, linked from the nav on all three main pages) is the single, ultimate source of truth for both content and formatting — it replaces the previous two-PDF setup (`AvinashResume.pdf` / `Avinash_Resume_2026.pdf`, both deleted) and the earlier `MASTERResume.docx` concept. No source `.docx` is currently on file for it, so the `formatting_preferences` field notes that tailored resumes should match this PDF's layout and content as closely as possible until Avi provides a source document to edit in place.

## Resume Tailoring Tool (`tailor/`, embedded in `tracker.html`)

A client-side-only feature: paste a company, role, and job description into the form in `tracker.html`'s "Tailor a Resume" section, and it generates a matched `.docx` resume and cover letter, downloaded directly in the browser. A second "Check Match Score" button scores the pasted JD against `master_resume_data.json` and shows a 0–100 fit score inline, without generating any documents. No backend, no build step.

- `tailor/matching-engine.js` scores each `master_resume_data.json` experience entry by keyword overlap against the pasted JD (industry tags count double), picks the top 5, and falls back to the 3 most recent roles if nothing scores. It deliberately excludes the Black Swan Yoga entry unless the JD mentions a specific yoga/fitness-studio signal (`BLACKSWAN_TRIGGER_WORDS`, deliberately narrow — generic business terms like "sales" or "customer-facing" were removed because they false-positived on unrelated technical JDs) — preserve that conditional-inclusion behavior if you touch this file.
- `tailor/scoring-engine.js` powers "Check Match Score". It blends `matching-engine.js`'s structured tag/skill overlap (70% weight) with raw-text cosine similarity (30% weight) into a single score, labeled Strong (≥65) / Partial (≥40) / Weak match. It reuses `tokenize`, `countTokens`, `scoreEntry`, and `shouldIncludeBlackSwan` from `matching-engine.js` — it has no module import, so `matching-engine.js` must be loaded first via a preceding `<script>` tag. The UI copy explicitly calls this a keyword/text-similarity heuristic, not a reasoning model — preserve that framing if you touch the score display.
- `tailor/doc-builder.js` builds `docx.Document` objects for the resume and cover letter from the selected entries. It skips any bullet flagged `NEEDS_DETAIL`/`NEEDS_VERIFICATION` — never remove that filter, since it's what stops unverified content from reaching a real generated resume. It also skips any bullet whose text matches a `SUSPICIOUS_PATTERNS` regex (`NEEDS_`, `PLACEHOLDER`, `unresolved`, etc.) as a second safety net in case unverified/internal-note text ever reaches this stage without the flag being set, logging a console warning when it does.
- `tailor/app.js` wires both buttons: "Generate Resume & Cover Letter" calls into `doc-builder.js` and downloads both `.docx` files via `docx.Packer.toBlob`; "Check Match Score" calls `computeMatchScore` from `scoring-engine.js` and renders the score inline.

Script load order in `tracker.html` matters and must stay: `matching-engine.js` → `scoring-engine.js` → `doc-builder.js` → `app.js`.

The `docx` library is loaded from a CDN `<script>` tag in `tracker.html`'s `<head>` (before any other script), pinned to a specific version — currently `https://unpkg.com/docx@8.5.0/build/index.umd.js`. **That exact path matters**: `docx@8.5.0`'s package.json points `main` at `build/index.umd.js`, not `build/index.js` — the latter 404s. If you ever bump the pinned version, re-check the package's actual `main`/`unpkg` field on unpkg before assuming the path still works, and confirm the loaded bundle still attaches `window.docx` (check that it's a UMD build, not an ESM-only one — newer `docx` versions dropped the UMD global build entirely).

`tailor/app.js` fetches `master_resume_data.json` with a plain relative `fetch()`, so this feature only works when `tracker.html` is served over HTTP(S) — opening it directly as a `file://` URL will fail the fetch (browsers block `file://` XHR/fetch to local files). Test locally with a static HTTP server, not by double-clicking the file.

## Conventions

- No sudo/admin needed for anything in this repo.
- Avi is on Windows (PowerShell), so prefer PowerShell-compatible instructions when giving him commands to run himself, though Claude Code's own tool calls handle git/file operations directly.
- Git author identity is `Avi Ravishankar <avikravi@gmail.com>` — already configured locally; don't reconfigure without being asked.
- Line endings: this repo is edited from both Windows and other environments; expect harmless LF→CRLF warnings from git on Windows — these are not errors.
- Keep commits scoped and the commit message descriptive of the actual content change (e.g. "Add application: Rivian", not "update").

## Keeping this file updated

When you make a structural change to this repo — a new page, a new data schema field, a new script, a change to the design tokens, a new top-level convention — update the relevant section of this file and `README.md` as part of that same commit. Don't wait to be asked. If you're unsure whether a change is "structural" enough to warrant a doc update, err toward updating.
