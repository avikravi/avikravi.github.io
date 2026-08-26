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
nano.png / nano-header.png  Source and resized product photos used in the case study header
                         (nano-header.png is referenced with an absolute /nano-header.png path
                         from hp/case-study/index.html, which lives two directories deep).
hp/                      All of Avi's HP application material, as of 2026-08-22. Every page here
                         shares one persistent left sidebar nav (see "The /hp section" below).
  index.html             URL: /hp — Home. Static reference table itemizing every skill/
                         requirement/responsibility from a specific HP job posting (Principal
                         Technical Product Marketing Manager, AI Solutions) as one row each.
                         No JS beyond the shared sidenav toggle, no localStorage, no edit UI —
                         the right-hand "How I Qualify" column is plain HTML that Claude Code
                         updates directly as Avi describes his experience in chat and it's
                         mapped to the matching row(s). As of 2026-08-23 this page was converted
                         from its own separate HP-brand-blue design to the shared light-editorial
                         tokens below (same as the other /hp pages) — the table's sticky header
                         and requirement links now use `--blue` (#1967b1) instead of HP's
                         #0096D6, and the old top brandbar strip was removed. HP-blue lives on
                         only in the persistent sidebar shared by every /hp page. Writing style
                         for the "How I Qualify" column: short, complete sentences. Never use a
                         dash (em dash or "--") to join two clauses; split into separate
                         sentences instead.
  case-study/index.html  URL: /hp/case-study. Working case study on the HP ZGX Nano AI Station
                         (feedback/positive-review scraper boxes, personal research, competitor
                         tracker). Originator of the light-editorial design system: as of
                         2026-08-21, index.html and projects.html were redesigned to match this
                         page's tokens, typography, and flat divided-list layout (see below). As
                         of 2026-08-22 its "Use Cases" tab was split out to hp/use-cases/ — this
                         page now has 4 tabs (Feedback, Positive Reviews, Research & Interviews,
                         Competitor Tracker), numbered 1-4; don't reuse "Box 4" for anything else
                         here since Use Cases' own text still refers to itself as Box 4 on its
                         own page, and this page's avi-review text references "Box 1"/"Box 2"
                         (Feedback/Positive Reviews) by number in several places — keep those two
                         numbers stable if you ever reorder tabs again.
  use-cases/index.html   URL: /hp/use-cases. 10-industry potential-use-case review for the ZGX
                         Nano (industry chip switcher, one panel per industry), split out from
                         case-study/index.html into its own page on 2026-08-22 so it could get
                         its own sidebar nav entry. Uses the same light-editorial tokens and
                         industry-panel/evidence-tag/strength-meter CSS as the case study — keep
                         both in sync if you touch that CSS. As of 2026-08-23, each industry
                         panel's "Avi's review" and "HP's claim" paragraphs are each wrapped in
                         their own `.example-card` (bordered, rounded, white for `.avi`, light
                         gray `#fafafa` for `.hp`) instead of flowing as plain divided text — a
                         deliberate one-off exception to the site's usual "flat divided list, no
                         boxed cards" rule (see Design system below), scoped to this page only,
                         per Avi's explicit request. Where a `<p class="cite">` follows a
                         `<p class="hp-claim">`, it's nested inside that same `.hp` card as a
                         footer (small text, divider line above) rather than floating on its own
                         — if you add a new industry with a citation, wrap it the same way.
                         Energy is the first chip/panel (reordered from Healthcare on
                         2026-08-23, also per Avi) — both the `industry-nav` button order and the
                         `industry-panel` div order were changed, and `ind-energy` carries the
                         initial `active` class on both. Its text references "Box 1, item NN"
                         and "Box 2, item NN" throughout, meaning specific numbered findings on
                         the case-study page; the panel-desc links to /hp/case-study for context.
  youtube/index.html     URL: /hp/youtube. Youtube playlist of Avi's AI/ML project videos — a
                         two-column layout (`.yt-layout`) at >=760px: a vertical "All Videos"
                         list (`.yt-list`, 300px wide) on the left, one mini card per video
                         (thumbnail + title, stacked top-to-bottom, scrolls internally past
                         640px tall), and the "now playing" iframe player (`.yt-player-col`)
                         filling the rest of the row on the right — deliberately much bigger
                         than the list, since that's the whole point of the layout (2026-08-23,
                         per Avi: put the list in what used to be dead white space next to a
                         small player, then let the player use the space that frees up). Below
                         760px both columns collapse to a single column via `flex-direction:
                         column`, with the player showing first (CSS `order`, not DOM order, so
                         markup order is list-then-player but visual order flips per breakpoint
                         — keep that in mind if you edit the HTML, since it no longer matches
                         reading order 1:1). List built from hp/youtube/videos.json (see below);
                         clicking an item swaps the iframe's src (autoplay) and highlights the
                         active item. No embedded YouTube Data API/key — see "The /hp section"
                         below for why. As of 2026-08-25, the first two items in the list are
                         hardcoded, non-YouTube videos, written directly into `#ytGrid`'s HTML
                         ahead of the dynamically-loaded YouTube ones (in this order: "P66 Vessel
                         Integrity Intelligence," then "Card Database App"): Loom embeds, each with
                         `data-embed="loom"` and `data-loom-id="..."` instead of `data-id`. Each
                         has a real thumbnail `<img>` pulled from the video itself — the guessed
                         CDN pattern (`cdn.loom.com/sessions/thumbnails/{id}-00001.jpg` /
                         `-with-play.gif`) 403s, but Loom's oEmbed endpoint
                         (`https://www.loom.com/v1/oembed?url=https://www.loom.com/share/{id}`)
                         returns a working `thumbnail_url` (`cdn.loom.com/sessions/thumbnails/{id}-
                         {hash}.gif`, an animated GIF) — hit that endpoint for any new Loom video's
                         id to get its real thumbnail before hardcoding a card, rather than
                         guessing the URL or leaving a plain color box. Only the P66 card carries a
                         small blue "Featured" tag next to its title (via a
                         `<span class="featured-tag">` inside `.video-card-title`) and is `active`
                         by default, so it's what plays when the page loads — Card Database App is
                         a plain, unfeatured list item. Avi explicitly rejected an earlier version
                         of the featured treatment (a separate bordered box above the whole
                         list/player layout) — he wanted it to stay inside the existing list, not
                         become a new visual element, so don't reintroduce a standalone featured
                         section without being asked again. The shared `playVideo(card)` function
                         (takes the clicked card element, not just an id) branches on
                         `card.dataset.embed` to build either a `loom.com/embed/{id}` or
                         `youtube.com/embed/{id}?list=...` src. It also updates the `#videoNote`
                         paragraph below the player: for a `loom` card it reads
                         `card.dataset.noteText`/`card.dataset.noteHref` if present (only the P66
                         card sets these, linking to `/hp/p66-example`) and clears the note
                         entirely if absent (Card Database App has no write-up page, so its note is
                         blank — don't invent one); for a `youtube` card it always shows "Open the
                         full playlist on Youtube." Dynamically-added YouTube cards get
                         `data-embed="youtube"` and are never active by default (the featured Loom
                         card owns that). `hp/youtube/videos.json`'s own order matters too — it's
                         currently `[Forecast 48, Academic Paper Review]` so the full on-page order
                         reads P66 → Card Database App → Forecast 48 → Academic Paper Review,
                         per Avi's explicit ordering request; keep the two hardcoded Loom cards and
                         this JSON order in sync if the sequence ever changes again. If Avi wants
                         to add another non-YouTube featured or regular video, copy one of these two
                         hardcoded `<button class="video-card">` blocks and wire up `playVideo`'s
                         `loom` branch accordingly — don't try to route a non-YouTube video through
                         `videos.json` (that file only supports YouTube IDs).
  youtube/videos.json    Manually maintained list of {id, title} for the /hp/youtube thumbnail
                         grid, fetched client-side with a plain relative fetch() (same file://
                         caveat as tailor/app.js — serve over HTTP(S) to test locally). Update
                         this file yourself whenever Avi says he's added a video to the actual
                         Youtube playlist; there's no automatic sync (see below). Thumbnails are
                         rendered via YouTube's public https://img.youtube.com/vi/{id}/hqdefault.jpg
                         — no API key needed for that part.
  ai-research/index.html URL: /hp/ai-research. Added 2026-08-23. Embeds Avi's summer 2026 Rice
                         University surgical-robotics research (a synthetic soft-tissue
                         deformation dataset/viewer) directly in-page via an <iframe> pointed at
                         https://avikravi.github.io/surgical-robotics-tissue-sim/dataset_viewer.html
                         — a live page in a separate repo, same GitHub Pages account, so no
                         X-Frame-Options/CSP block (verified: `curl -sI` on that URL returns no
                         framing-restriction headers). The iframe'd page keeps its own dark
                         teal design system; don't try to reskin it from here. A "sim-note" link
                         below the iframe opens the same URL in a new tab as a fallback. This is
                         the same project index.html/projects.html already link to externally
                         under "Research" in their own nav (see "Nav bar consistency" below) —
                         this page just embeds it instead of linking out.
  p66-example/index.html URL: /hp/p66-example. Added 2026-08-23 as a sixth flat sidebar item
                         (briefly visually nested under "AI Research" via a `.hp-nav-sub` indent
                         class, same day — Avi asked for it flat instead, so that class was
                         removed from all six /hp pages; don't reintroduce it unless asked again).
                         Describes
                         an independent pressure-vessel integrity prototype (ML corrosion
                         prediction, fleet risk dashboard, ASME/API standards reference) from
                         github.com/avikravi/p66-vessel-integrity — explicitly NOT affiliated with
                         Phillips 66, built on synthetic data only; keep that disclaimer visible if
                         you edit this page's copy (the embedded app repeats its own version of
                         this disclaimer in a banner at the top, so it's stated twice by design).
                         The repo is a Next.js app with no `output: 'export'` config, so it can't
                         be a static GitHub Pages embed like hp/ai-research's — instead, as of
                         2026-08-23 Avi deployed it to Vercel (`.app-embed` iframe pointed at
                         https://p66-vessel-integrity.vercel.app, the stable production domain —
                         not the per-deployment `*-<hash>-avikravi-gmailcoms-projects.vercel.app`
                         URL Vercel also shows, which changes on every deploy). Verified via
                         `curl -sI` that Vercel doesn't send X-Frame-Options/CSP frame-ancestors,
                         so it frames fine. If Avi redeploys under a different Vercel project/team
                         and the domain changes, update the iframe `src` and the two `.app-note`
                         links (same URL, three places in this file) together.
hp-pmm-worksheet.html    Thin meta-refresh redirect stub → /hp (old pre-2026-08-22 URL, kept so
                         any existing links don't 404).
zgx-nano-case-study.html Thin meta-refresh redirect stub → /hp/case-study (old pre-2026-08-22
                         URL, kept so any existing links don't 404).
README.md               Human-facing docs
CLAUDE.md               This file
```

## Design system — DO NOT change without being asked

**Two design systems now coexist in this repo, split by page.** Don't mix their tokens.

### Light-editorial system (`index.html`, `projects.html`, and every page under `hp/`)

As of 2026-08-21, `index.html` and `projects.html` were redesigned to match `hp/case-study/index.html`'s (formerly `zgx-nano-case-study.html`) clean, light, editorial look, at the user's explicit request — all original wording/content was preserved, only the visual system changed. As of 2026-08-23, `hp/index.html` (the worksheet) was converted to the same tokens too — every page under `hp/` now shares this system, not just three of the five. `hp/case-study/index.html` remains the source of truth for these tokens:

```css
--bg: #ffffff;
--ink: #191919;
--ink-soft: #3d3d3d;
--ink-faint: #767676;
--line: #e5e5e5;
--blue: #1967b1;
```

Font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`

Shared conventions across these pages:
- Flat, thin-bordered nav (`border-bottom: 1px solid var(--line)`) — black wordmark logo, uppercase nav links in `--ink-faint`, black underline "active" state, solid black "Download Resume" pill button (`index.html`/`projects.html` only — the `hp/` pages use the persistent left sidebar instead, see below)
- No background animation, no gradients, no glow/blur effects — plain white background throughout
- Page header pattern: optional `.eyebrow` (small uppercase label, `--ink-faint`, 13px, letter-spacing 0.04em), bold black `h1`, `.dek` subtitle in `--ink-faint` (15.5-16px)
- Section pattern: `.panel-title` (bold black `h2`-equivalent) + `.panel-desc` (faint subtitle with a bottom border divider)
- Content is flat divided lists (`.fitem` — `border-top: 1px solid var(--line)` between entries), not boxed/shadowed cards — this is the key visual difference from the dark system below. `hp/index.html`'s table follows the same instinct: no zebra-striped row backgrounds, just `border-bottom: 1px solid var(--line)` between rows. **Exception:** `hp/use-cases/index.html`'s `.example-card` boxes (added 2026-08-23, per Avi's explicit request) — bordered, rounded, white/light-gray cards for each "Avi's review"/"HP's claim" block. This is a deliberate one-off, not a precedent for adding cards elsewhere in the light-editorial system.
- Small pill tags (`.tag-co`, `.chip`) for categories/tech stacks: subtle border, no fill or a very light `#fafafa` fill, never a colored gradient

If asked to add a new page or extend `index.html`/`projects.html`, copy tokens and conventions from `hp/case-study/index.html` or these two pages — not from `tracker.html`.

## The `/hp` section (`hp/`)

As of 2026-08-22, every page under `hp/` (`index.html`, `case-study/index.html`, `use-cases/index.html`, `youtube/index.html`, `ai-research/index.html`, and `p66-example/index.html` as of 2026-08-23) shares one persistent left sidebar nav (`.hp-shell` / `.hp-sidenav` / `.hp-main` etc. — the CSS block is duplicated verbatim into each page's `<style>`, since there's no build step to share it from one file). This sidebar is deliberately its own design layer, sitting *outside* the light-editorial system every `/hp` page's content area now uses (see above): a dark (`#14161b`) fixed-left sidebar (232px) with the HP brand blue (`#0096D6`, via `var(--hp-blue, #0096D6)` so it renders correctly even on pages whose own `:root` doesn't define `--hp-blue`) as the active-link/accent color — this is the only place `--hp-blue` still appears; the content area of every `/hp` page uses `--blue` (#1967b1) like `index.html`/`projects.html`. Links, in order, all flat/same-level (six total): "Home - Job Fit" (`/hp` — relabeled from plain "Home" on 2026-08-23 so the sidebar itself hints at what that page is), ZGX Nano Case Study (`/hp/case-study`), Use Cases (`/hp/use-cases`), Youtube (`/hp/youtube`), AI Research (`/hp/ai-research`), P66 Example (`/hp/p66-example`). Deliberately **no** link back to the main site (`/`) — Avi removed it on 2026-08-22 so the sidebar doesn't distract a reader who's evaluating this HP-specific material. Don't re-add one unless he asks.

Every `/hp` page's `.wrap` uses the same `max-width: 1180px; margin: 0 auto; padding: 0 24px;` as of 2026-08-23 (matching `index.html`/`projects.html`) — before that, the four pages had drifted to three different widths (1100px, 1180px, 900px) as they were built one at a time. `h1` is `32px` / `line-height: 1.15` and `.dek` is `15.5px` / `max-width: 620px` on every `/hp` page too, for the same reason. `hp/use-cases/index.html`'s prose content is wrapped in a `.panel-body { max-width: 780px; }` div (matching `hp/case-study/index.html`'s existing convention) so its paragraphs don't stretch edge-to-edge now that `.wrap` is wider — the `industry-nav` chip grid and `balance-note` are inside that same wrapper. If you touch any `/hp` page's header typography or `.wrap`, check the other four match.

Mobile (`max-width: 880px`): the sidebar becomes an off-canvas drawer (`transform: translateX(-100%)` by default, `.open` slides it in), triggered by a sticky "Menu" hamburger button (`#hpNavOpen`) that appears at the top of `.hp-main`, with a dark scrim (`#hpNavScrim`) behind it and a close button (`#hpNavClose`) in the drawer header. The toggle JS is a small inline `<script>` block at the end of each page's `<body>`, using those three element IDs plus `#hpSidenav` — keep the IDs consistent if you copy this block to a new `/hp` page.

If you add another `/hp` page, copy the entire `.hp-shell`/`.hp-sidenav`/etc. CSS block and the matching HTML structure + toggle `<script>` from `hp/ai-research/index.html` or `hp/youtube/index.html` (the simplest of the five), add a new `<a class="hp-nav-link">` row to the nav list on **all** `/hp` pages (including the new one, marked `active`), and use an absolute path (`/hp/whatever`) for its URL and for any cross-page links, since these pages live at different folder depths.

Since GitHub Pages serves a directory's `index.html` for both `/hp` and `/hp/` (no Jekyll pretty-permalink magic needed), every `/hp` page is a folder (`hp/case-study/index.html`, not `hp/case-study.html`) so its clean URL works. The old root-level `hp-pmm-worksheet.html` and `zgx-nano-case-study.html` are now thin `<meta http-equiv="refresh">` redirect stubs pointing at `/hp` and `/hp/case-study` respectively — update those stubs' targets if a `/hp` page's URL ever changes again.

### `/hp/youtube`'s video list is manually maintained, not live-synced

`hp/youtube/videos.json` is a plain hand-maintained array — it is **not** kept in sync with the real Youtube playlist automatically. This was a deliberate tradeoff, not an oversight: a client-side `fetch()` of Youtube's own playlist RSS feed (`https://www.youtube.com/feeds/videos.xml?playlist_id=...`) is blocked by CORS from a page hosted on `avikravi.github.io` (tested directly — `fetch` throws `Failed to fetch`), and the only way to enumerate a playlist's contents live from the browser is the Youtube Data API v3, which needs an API key. A referrer-restricted key is a common pattern for static sites but adds setup (Google Cloud project, quota risk if the key leaks) that wasn't worth it for a two-video personal playlist. So: when Avi says he's added a video to the playlist, fetch its title (`WebFetch` on the playlist's RSS feed URL works fine for reading, just not for a same-origin browser `fetch()`) and append a `{ "id": "...", "title": "..." }` entry to `hp/youtube/videos.json` yourself, in playlist order. Thumbnails need no maintenance — they're pulled live from Youtube's public `https://img.youtube.com/vi/{id}/hqdefault.jpg`, which works for any public video ID with no key.

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
