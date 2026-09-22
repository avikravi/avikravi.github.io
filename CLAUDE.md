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
                         numbers stable if you ever reorder tabs again. Competitor Tracker was
                         refreshed 2026-08-25 for a presentation, then again 2026-08-26 for
                         interview prep: added AMD's Ryzen AI Halo (first non-GB10 competitor,
                         ships with Windows as an option, unlike every GB10 box), ServeTheHome's
                         follow-up review of the shipping Lenovo ThinkStation PGX, and NVIDIA's own
                         Feb 25, 2026 DGX Spark Founders Edition price hike ($3,999 to $4,699,
                         memory supply constraints) — note that NVIDIA's own post explicitly says
                         that price change does NOT apply to OEM GB10 systems like the ZGX Nano, so
                         don't conflate the two if this gets updated again. Also updated the May 31
                         RTX Spark entry to note HP itself is a confirmed RTX Spark OEM partner for
                         fall 2026. Feedback/Positive
                         Reviews were re-checked against fresh search results but no new
                         independent ZGX-Nano-specific reviews turned up since the original Oct/Nov
                         2025 batch (Notebookcheck, ServeTheHome, StorageReview, Global Nerdy) — one
                         candidate claim (VRM temperatures under sustained overclock, from
                         aigigabit.com) was deliberately excluded because that domain now redirects
                         to an unrelated finance subdomain and couldn't be verified directly; don't
                         add it back without a trustworthy live source.
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
                         below for why. As of 2026-08-25, the first three items in the list are
                         hardcoded, non-YouTube videos, written directly into `#ytGrid`'s HTML
                         ahead of the dynamically-loaded YouTube ones (in this order: "P66 Vessel
                         Integrity Intelligence," then "Teaching Robots Tissue Mechanics with ML,"
                         then "Card Database App"): Loom embeds, each with
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
                         by default, so it's what plays when the page loads — the other two Loom
                         cards are plain, unfeatured list items. Avi explicitly rejected an earlier version
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
                         entirely if absent (the other two Loom videos have no write-up page, so
                         their note is blank — don't invent one); for a `youtube` card it always
                         shows "Open the full playlist on Youtube." Dynamically-added YouTube cards
                         get `data-embed="youtube"` and are never active by default (the featured
                         Loom card owns that). `hp/youtube/videos.json`'s own order matters too —
                         it's currently `[Forecast 48, Academic Paper Review]` so the full on-page
                         order reads P66 → Teaching Robots Tissue Mechanics with ML → Card Database
                         App → Forecast 48 → Academic Paper Review, per Avi's explicit ordering
                         request (five videos total as of 2026-08-25); keep the three hardcoded
                         Loom cards and this JSON order in sync if the sequence ever changes again.
                         If Avi wants to add another non-YouTube featured or regular video, copy
                         one of these three hardcoded `<button class="video-card">` blocks and wire
                         up `playVideo`'s `loom` branch accordingly — don't try to route a
                         non-YouTube video through `videos.json` (that file only supports YouTube
                         IDs).
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
                         and the domain changes, update the iframe `src` and the "Open the app in
                         its own tab" link inside `.app-note` (same URL, two places in this file —
                         the other `.app-note` link points to the GitHub repo, not Vercel, so leave
                         that one alone) together.
  30-60-90/index.html    URL: /hp/30-60-90. Added 2026-08-27, substantially expanded same day,
                         then substantially CUT BACK DOWN on 2026-09-16 per Avi's explicit
                         feedback that the expanded version read as "slop and filler" for its
                         real audience (a PMM Director) — don't re-expand it back toward prose
                         paragraphs, multi-column grids, or flow-diagram visuals without being
                         asked again. A 30/60/90-day plan for the actual HP Principal TPMM, AI
                         Solutions role, written for post-interview follow-up. First page under
                         the sidebar's new "Post Interview" grouped section (see "The /hp section"
                         below) rather than the flat top-level list the other six pages use.
                         **Voice, as of 2026-09-16: terse, active voice, bullet-first.** "I run,"
                         "I build," "I ship" — not "this plan ships" or descriptive scene-setting.
                         Every section is a short intro line (if any) plus a flat bullet list; no
                         multi-sentence narrative paragraphs anywhere on this page. If you edit
                         this page, match that register — don't let it drift back toward the
                         longer, explain-everything tone the rest of this file's older notes
                         describe (those notes are kept below for history but no longer describe
                         the current page).
                         **No compensation figures anywhere on this page, or anywhere else on the
                         site** — Avi explicitly asked for this after an earlier chat turn (not the
                         page itself) mentioned a number; never reintroduce one.
                         **"Open Questions I Confirm First" is the load-bearing new section**
                         (2026-09-16, directly per Avi's ask to "leave blanks that I need to
                         clarify with the Directors and managers and teams when I meet with them
                         next"): a `.confirm-box` containing a `.confirm-list` of short prompts,
                         each ending in a literal visual blank (`<span class="confirm-blank">`, a
                         fixed-width dashed underline — give it an explicit `width`, not just
                         `flex: 1 1 90px`, since several instances live inside plain `.plan-list`
                         `<li>`s that aren't flex containers and the span collapses to zero width
                         without one; this was a real bug caught and fixed the same day). Two more
                         `.confirm-blank`s appear inline inside "Also Worth Exploring" bullets.
                         Don't fill these blanks in yourself with invented answers — they exist
                         because Avi doesn't have the information yet and the page says so
                         honestly; only Avi updates them, after he actually has the conversation.
                         Current section order: page-header (with the `.arc-timeline` visual, kept
                         from the original build — a 4-milestone Day 1/30/60/90 progress bar,
                         CSS-only, collapses to a stacked list below 640px) → Open Questions I
                         Confirm First (new, see above) → Day 1: Oil & Gas Hypotheses (kept, but
                         each `.hypothesis-card` trimmed to a one-line Hypothesis/Build/Proves —
                         still explicitly extensions of the real, already-shipped
                         `/hp/p66-example` prototype, not net-new invented claims) → The 90-Day
                         Arc (three `.phase-block` sections, Days 1-30/31-60/61-90; each phase is
                         now just ONE flat `.plan-list` of 5-6 bullets plus a single bold
                         `.phase-target` line — the old per-phase Goals/Key Activities/
                         Deliverables/Success Metrics four-way split and the `.plan-grid` CSS it
                         used are both gone, collapsed into that one list+target pattern) → Metrics
                         That Matter (kept, same `.metrics-grid` of 5 `.metric-tile` cards, north
                         star "Revenue-Qualified Pipeline Influenced" plus 4 supporting KPIs, defs
                         trimmed to one line each — still deliberately NOT fake live numbers, since
                         these are proposed/illustrative until HP leadership sets real thresholds;
                         don't add fabricated data to these tiles) → Also Worth Exploring (new,
                         2026-09-16 — a single flat `.plan-list` merging what used to be four
                         separate sections: the academic-channel idea grounded in Avi's real Rice
                         TA role, the honest "HP is 1 of 6+ GB10 OEMs" read, the NVIDIA-dependency
                         note, and formalizing the case study's scrape→score→draft→review→publish
                         pattern — each now one bullet instead of its own section with an intro
                         paragraph) → footer. **Cut entirely on 2026-09-16, do not re-add without
                         being asked:** the "Guiding Principles" section (5 bullets of narrative
                         self-description — its one genuinely useful idea, naming hands-on gaps
                         honestly, now lives in the Open Questions section instead, which shows
                         it rather than states it); "Expanding the Channel: Academia" and "The
                         Ecosystem: NVIDIA, OEMs, and Channel Partners" as standalone sections
                         (content survives, compressed into Also Worth Exploring); both
                         `.flow-diagram` instances (the 5-step positioning-loop diagram and the
                         4-step Plan→Build→Signal Check→Re-baseline cadence diagram) along with
                         the `.flow-diagram`/`.flow-step`/`.flow-arrow`/`.flow-loop-note` CSS that
                         supported them — the ideas behind both survive as single bullets, but the
                         visual diagrams themselves were judged as filler bulk relative to the
                         plan content they illustrated; the `.principles-list`, `.plan-grid`, and
                         `.plan-col-title` CSS rules were removed for the same reason (no longer
                         used anywhere on the page).
                         The plan is written to be internally consistent with the rest of the site:
                         it references the real gaps documented on `/hp` itself (no battlecards/
                         reference architectures yet, several open-source models/frameworks not yet
                         hands-on), cites the methodology of the ZGX Nano case study as the standard
                         for any new benchmark or content claim, and the Day 1 hypotheses explicitly
                         build on `/hp/p66-example` rather than inventing unrelated new claims.
                         Doesn't use the `--hp-blue` accent anywhere in its content area, consistent
                         with every other `/hp` page. If you add more visual components to this
                         page, reuse `.metrics-grid`/`.hypothesis-grid`/`.confirm-box` rather than
                         inventing a new pattern — and bias toward a bullet list over a new visual
                         component at all, given the 2026-09-16 brevity mandate above.
  object-detect-summary/index.html  URL: /hp/object-detect-summary. Added 2026-09-20 as a
                         6-level placeholder breakdown, expanded 2026-09-21 to 10 levels, then
                         completely rewritten 2026-09-21 with Avi's real project content (he
                         supplied a full reference doc — `~/Downloads/project_reference.md` — plus
                         the actual code/images/CSVs from his local `objectdetect/` project folder,
                         which sits untracked alongside this repo; see `.gitignore`). This is a
                         real take-home deliverable for an HP Principal TPMM, AI Solutions
                         interview (round 4): a progressive 10-level object detection/counting
                         project, classical CV -> learned classifiers -> deep learning ->
                         open-vocabulary detection -> video tracking -> hardware-scaling analysis.
                         Page structure: dek states the assignment context (no compensation/dates,
                         per the site's usual rule — see Conventions below); an "Environment"
                         panel documents the real constraint that shaped every later level (Intel
                         Mac, Python 3.11, `torch==2.2.2` ceiling since PyTorch dropped Intel Mac
                         support at 2.3, which cascades into numpy `<2`, opencv-python `<5`, and
                         `transformers==4.46.3` pins — Level 6's own dependency-conflict story
                         links back here rather than repeating it); a "Level Roadmap" `.level-table`
                         (Level/Approach/Status, styled like hp/index.html's job-fit table) with
                         all ten rows, every one `Done`; an "Overall Narrative Arc" panel
                         reproducing Avi's own framing verbatim (the L1->L10 technical progression,
                         and the "every level has an honest documented limitation" theme running
                         through the whole project) — if a level's content changes, keep this
                         panel's per-level callouts (tilted faces/L1, zero-detection/L2,
                         wrong-viewpoint/L3, missing vocabulary/L4, language-matching/L5,
                         compute cost/L6, motorcycle filter/L7, approximate speed/L8) in sync with
                         what that level's own page actually says. Below that, a `.panel-empty`/
                         `.empty-tag` placeholder ("Slides Coming Soon") still waits for the actual
                         deck — unrelated to the 10 levels, don't remove it just because the levels
                         are now filled in.
  object-detect-level-1/index.html through object-detect-level-10/index.html  URLs:
                         /hp/object-detect-level-1 through -10. All ten fully written up
                         2026-09-21 from Avi's real project (code, results, and — for most levels —
                         actual demo images copied in from his local `objectdetect/` folder as
                         siblings of each page's `index.html`; e.g. `hp/object-detect-level-1/
                         output.jpg`). Large source assets (some images were 8256x5504 / 20MB+;
                         one was a PNG mislabeled with a `.jpg` extension; videos ran 7.7MB-626MB)
                         were NOT committed as-is — oversized/mislabeled images were resized and
                         properly re-encoded as JPEG with macOS `sips` (max ~1600px wide, ~75-80%
                         quality) before copying in, and the Level 7/8 videos were left out
                         entirely (see below — Avi is uploading them to YouTube instead). Every
                         level with a result image also got its matching **unannotated original**
                         copied in and shown as a `.image-pair` "Before"/"After" (added 2026-09-21
                         per Avi's request) — matching the raw source to the right result took real
                         visual verification (e.g. Level 2's `people1.jpg`/`people4.jpg` inputs
                         needed to be checked against `output1.jpg`/`output4.jpg` to confirm which
                         paired with which; don't assume filename order implies pairing on a level
                         you haven't verified).

                         **CAUTION — these 10 pages are generated from one local Python script**
                         (in a scratchpad dir, not tracked in this repo) that rewrites all 10 files
                         at once from hardcoded per-level content strings. This already caused one
                         real problem (2026-09-21): Avi opened `hp/object-detect-level-2/index.html`
                         himself and manually removed its "Flag for Avi" `.confirm-box` (a plain
                         `git commit -m "Edits"`, not a Claude Code change), and a subsequent
                         Claude Code regeneration of all 10 pages — done to reorder Level 3's
                         content, unrelated to Level 2 — silently re-added that box, since the
                         generator script still had the old content and had no way to know about
                         Avi's out-of-band edit. Caught and re-fixed the same session, but the
                         lesson stands: before regenerating any of these pages from such a script,
                         check `git log --oneline -- hp/object-detect-level-*` (and the summary
                         page) for commits not authored by that regeneration process, and fold
                         any real edits found there into the script first — don't assume the
                         script's last-known content is still accurate just because you wrote it.

                         **Anomaly-tag audit (2026-09-22).** Avi liked the `.anomaly-tag` treatment
                         enough to ask for it "wherever it applies" across all ten levels, which
                         prompted a full re-read of every level's actual content against a specific
                         definition: an anomaly case is a *deliberate, out-of-domain probe* — Avi
                         intentionally threw something unrelated to the project's real domain at a
                         working detector just to see what it would do, expecting (and getting) a
                         null/negative result. Only two qualify: Level 3's aerial photo and Level
                         7's Clip 3 (oranges), both already tagged. Cases that look similar but
                         don't qualify, on purpose — don't tag these if revisiting this later: Level
                         2's zero-detection portrait (a real failure mode on an in-domain subject,
                         not an unrelated probe), Level 4's COCO vocabulary gap (the project's
                         central finding, not a side-test), Level 5's zero-detection on the
                         synthetic render (one of four *systematic* test images reused across
                         Levels 5-6, not a one-off curiosity), and Level 8's uncalibrated Clip 4
                         speeds (a data-quality caveat within the same clip type, already covered
                         by its own `.balance-note`). If a genuinely new anomaly case is added to
                         any level later, apply `.anomaly-tag` (text) or `.video-anomaly-tag`
                         (media tile) using this same test, not just "this result was unexpected."

                         **Terminal output (added 2026-09-21).** Levels 1-6 each show a real,
                         verified "Terminal output" block (`.output-label` + `.code-block.terminal`
                         — same dark container as the source-code `.code-block`s, but with green
                         `#7ee787` text instead of gray, to read as "what it printed" rather than
                         "what I wrote") right after their image(s). This is genuinely captured
                         console output, not invented: Avi's `objectdetect/` project has a working
                         Python 3.11 venv, so each level's detection script was re-run from a
                         sanitized copy (original `cv2.imshow`/`cv2.waitKey`/`cv2.destroyAllWindows`
                         calls stripped out first, since those block on a GUI window and would have
                         popped a live window on Avi's screen if left in) against the exact same
                         input image already on the page, and the real stdout was pasted in
                         verbatim. Re-running caught two inaccuracies inherited from Avi's own
                         reference doc that the initial page copy had repeated without independently
                         verifying against the actual output image: Level 2's "success case" is
                         `people1.jpg` -> 4 pedestrians detected (not "6-8" as the reference doc
                         estimated), and Level 5's `output1.jpg` result is person/helmet/electrical
                         cabinet/pallet jack — it does NOT include "safety vest" despite that being
                         one of the model's searched-for classes; the page copy was corrected to
                         match the verified console output instead of the unverified prior claim.
                         If any level's image or claimed numbers are ever edited again, prefer
                         re-running the underlying script (from within its own `objectdetect/levelN/`
                         directory, with a sanitized no-GUI copy, e.g. `sed -e '/cv2\.imshow/d' -e
                         '/cv2\.waitKey/d' -e '/cv2\.destroyAllWindows/d'`) over trusting prose
                         descriptions, exactly like this pass did. Levels 7-10 don't have a terminal
                         output block: 7-8 are video (reprocessing a full clip to capture its
                         console summary is a heavier, slower job than a single image and hasn't
                         been done yet — a reasonable follow-up if Avi wants it); 9-10 are writeups
                         with no script to run. Content by level:
                         L1 Haar Cascade (classical, fixed rules, faces) — Done. Before/after pair:
                         `face_sample.jpg` (original) / `output.jpg` (annotated). Terminal output:
                         8 faces detected, with each box's real pixel coordinates.
                         L2 HOG+SVM (learned classifier, hand-crafted features, pedestrians) — Done.
                         Two separate before/after pairs under their own subheadings: "Success case"
                         (`people1.jpg` / `output1.jpg`, terminal output: 4 pedestrians after NMS)
                         and "Zero-detection case" (`people4.jpg` / `output4.jpg`, terminal output:
                         0 pedestrians — captioned as identical to the input, since nothing was
                         detected to draw). IMPORTANT DISCREPANCY (context, not currently shown on
                         the page): Avi's project notes describe the zero-detection case as "a wide
                         traffic-camera shot with small, distant cyclists," but the actual saved
                         file is a close-cropped group portrait, not a traffic scene — the page
                         describes what the image actually shows (a crop with no legs/torso for the
                         pedestrian detector to match) instead of the notes' description. An
                         on-page `.confirm-box` ("Flag for Avi") originally called this mismatch out
                         explicitly; Avi read it and removed the box himself (2026-09-21, a manual
                         edit — see git history, not a Claude Code change) without supplying a
                         replacement cyclist image, so treat this as acknowledged/accepted rather
                         than an open item — don't re-add that confirm-box. If Avi ever does supply
                         a real cyclist image (with its own unannotated original), swap both in as
                         the zero-detection case instead of the current portrait.
                         L3 YOLOv8 general detection (COCO, 80 classes) — Done. Two results, in
                         this order (per Avi, 2026-09-22): the highway-camera result comes first,
                         shown as a before/after pair (`traffic.jpg` / `traffic_output.jpg`, 9
                         vehicles — terminal output confirms the exact real Ultralytics print
                         format, "7 cars, 1 bus, 1 truck", matching the page's prose exactly);
                         the aerial/broccoli-false-positive result comes second, explicitly labeled
                         as an anomaly with an inline `.anomaly-tag` badge (Avi specifically liked
                         this treatment, 2026-09-22 — amber `#a8461f`, `9.5px` uppercase text,
                         `3px 8px` padding, pixel-identical to Level 7's `.video-anomaly-tag`
                         values so the two read as the same design element even though one is a
                         plain inline-block span next to `.panel-title` text and the other is
                         absolutely positioned over a video tile — there's no image here to
                         overlay, hence the two variants) — Avi confirmed he isn't sending that
                         image, so this is text-only by design, not a gap: no `.confirm-box`
                         asking for it anymore. If Avi ever does send the aerial photo, add it as
                         a normal `.level-image` (no "before" needed if he only has the annotated
                         result) but keep the anomaly framing and second position, matching how
                         Level 7's Clip 3 anomaly is still visually flagged even though it has
                         real footage. `.balance-note` ties the two results together (viewpoint
                         sensitivity) and still works regardless of which one is listed first.
                         L4 YOLOv8 on a real manufacturing scene — Done. The project's pivot point:
                         before/after pair (`warehouse.jpg` / `output.jpg`), result is `person: 3`
                         and nothing else (terminal output confirms this exactly), `.balance-note`
                         explains COCO's missing industrial vocabulary. Don't soften this framing —
                         it's what the rest of the project (L5, L6) directly responds to.
                         L5 YOLO-World (open-vocabulary) — Done. Iteration history as a
                         `.result-list` (confidence threshold, over-generic "box" term, imgsz),
                         "final clean result" shown as a before/after pair (`warehouse1.jpg` /
                         `output1.jpg` — person/helmet/electrical cabinet/pallet jack all correctly
                         boxed; terminal output verified this is `person: 4, helmet: 2, electrical
                         cabinet: 2, pallet jack: 1` — see the "IMPORTANT" note above, this page
                         copy used to also claim "safety vest" and that was wrong), plus a third,
                         separate image (`output3.jpg`, no "before" pair — it's already unannotated
                         since nothing was detected, terminal output confirms 0 objects) showing
                         zero detections on a synthetic 3D-rendered warehouse scene, deliberately
                         set up as a cliffhanger into Level 6.
                         L6 Grounding DINO (stronger open-vocabulary) — Done. Dependency-conflict
                         story (transformers 5.x needs torch>=2.5, pinned to 4.46.3 instead — links
                         back to the Environment panel on Summary rather than repeating it), custom
                         cross-class duplicate suppression, and the "standout result": its own
                         before/after pair (`warehouse3.jpg` / `output3.jpg`, both local to this
                         page's folder — `warehouse3.jpg` was recovered from a PNG mislabeled
                         `.jpg` and properly re-encoded) showing cardboard box/crate/pallet
                         truck/cabinet all correctly found (terminal output gives the precise
                         breakdown: `hand pallet truck: 1, cardboard box wooden crate: 2, electrical
                         cabinet: 4, cardboard box: 1`), followed by a plain-text callout (not a
                         second image) noting Level 5's YOLO-World found nothing on this exact same
                         image, linking to `/hp/object-detect-level-5`. This replaced an earlier
                         version that cross-referenced Level 5's image directly via an absolute
                         path — now each level's images are self-contained in its own folder, which
                         is more robust if either page's assets ever change.
                         L7 Video object tracking + counting (YOLOv8 `model.track()`, ByteTrack) —
                         Done. Real result (46 unique vehicles across a ~800-frame clip) and a
                         debugging note about an early motorcycle-filtering oversight (COCO class
                         ID 3 missing from the filter dict, not a detection failure). As of
                         2026-09-21, a "Demo Clips" section embeds all 5 of Avi's real tracked
                         YouTube videos (titled "Level7 - Output1" through "Output5" on YouTube
                         itself, confirming the numbering) — 3 standard landscape uploads (Clips 1,
                         4, 5: `UWup7HqeD7o`, `aryhtIwIh0s`, `cdDmq56dR7g`) and 2 YouTube Shorts
                         (Clips 2, 3: `9s6Aw3lQFgc`, `X-R83Jnfg38`). Laid out as a `.video-grid`
                         (CSS grid, `align-items: start` so mixed 16:9/9:16 tiles keep their own
                         natural height instead of stretching to match row neighbors) rather than
                         the original stacked-with-captions layout, which Avi found too loose; each
                         tile is a small numbered `.video-num` badge overlaid top-left on the
                         `.video-embed` instead of a separate caption line, landscape tiles plain
                         `.video-embed`, Shorts get the `.video-embed.vertical` modifier
                         (`aspect-ratio: 9/16`). **Sized large (2026-09-22, per Avi: "way bigger" /
                         "don't worry too much about the layout being perfect"):** `.video-grid` is
                         `repeat(2, 1fr)` at up to `max-width: 1100px` (not the usual 720px text
                         column — video needs the extra width, prose doesn't), collapsing to a
                         single full-width column below `760px` viewport width. This intentionally
                         trades the earlier tighter 3-column layout for real watchability; don't
                         re-tighten it back down without being asked again. **Clip 3 is a
                         deliberate anomaly test, not
                         a mistake** — Avi threw a random video of oranges dropping at the tracker
                         to see whether it would find anything in a scene it wasn't built for; it
                         found nothing, which is the correct, honest result (and notably "orange" is
                         genuinely one of COCO's 80 classes, so it wasn't a rigged test — the model
                         still came up empty on real footage, echoing Level 3's aerial-photo lesson).
                         This reasoning is stated up front in the "Demo Clips" `.panel-desc`, before
                         the grid, per Avi's request, and Clip 3's tile carries an amber
                         `.video-anomaly-tag` ("Anomaly test") badge in the top-right corner so it
                         reads as intentional at a glance, not a stray/broken video. If more clips
                         are ever added, keep the grid pattern (and flag any other intentionally
                         off-topic test clip the same way) rather than reverting to a stacked list.
                         Every iframe fires the same `embed_viewed` GA4 event on lazy `onload` that
                         `hp/ai-research`/`hp/p66-example` already use (`embed_name` values
                         `level7_clip_1` through `_5`) — see Analytics below.
                         L8 Video speed estimation + CSV export — Done. Real per-vehicle data
                         tables (`.data-table`) pulled directly from `objectdetect/level8/
                         speed_data1.csv` and `speed_data4.csv` (both copied into
                         `hp/object-detect-level-8/` as real downloadable artifacts via
                         `.download-link`s — they're tiny, a few KB, unlike the videos). The
                         calibration-honesty point is made with REAL data, not just prose: clip 1's
                         speeds are plausible (single digits to low 30s mph), clip 4's are not
                         (one vehicle averaging 157mph, another peaking past 275mph) — same
                         uncalibrated pixel-to-mph formula, no camera calibration in either case.
                         Don't swap in more "flattering" numbers if this section is ever edited;
                         the implausible clip 4 numbers are the whole point. As of 2026-09-22, a
                         "Demo Clips" section (same pattern as Level 7) embeds all 4 of Avi's real
                         YouTube clips, in his given order (`P1r6nl-ANTk`, `NNSnomdiG68`,
                         `P7z4Tpds3x8`, `MFsgUAnEmFs`) — the old `.confirm-box` was removed. Laid
                         out as a 2x2 `.video-grid` — same shared class as Level 7, not a separate
                         modifier (a `.video-grid.pair` variant existed briefly on 2026-09-22 but
                         was removed the same day: its two-class selector had higher specificity
                         than the plain `.video-grid` mobile media query, so `.pair`'s desktop
                         `repeat(2, 1fr)` silently won even under the `max-width: 760px` breakpoint
                         and mobile stayed stuck at 2 cramped columns — caught by literally checking
                         mobile in the browser pane, not just eyeballing desktop. Now both Level 7
                         and Level 8 just use bare `.video-grid`, which is `repeat(2, 1fr)` at up to
                         `1100px` and collapses to one column below 760px, no specificity conflict
                         possible. If a future level needs a different column count, add the
                         variant rule *inside* the same media query it needs to win against, not as
                         a same-specificity-or-lower rule outside it).
                         All 4 initially showed "This video is private" right after embedding —
                         confirmed a YouTube-side visibility setting, not an embed-code bug, by
                         checking directly in the browser pane (which has real network access,
                         unlike this environment's `curl`, which gets blanket-blocked by YouTube's
                         oEmbed endpoint regardless of a video's actual status — don't trust
                         `curl`/oEmbed checks against youtube.com from here, verify in the browser
                         pane instead). Avi set all 4 to Public in YouTube Studio the same day and
                         confirmed via the live production site (not just localhost) that all four
                         now play correctly, titled "Level8 - Output1" through "Output4" matching
                         tile order 1-4.
                         L9 Writeup: scaling to the HP ZGX Nano AI Station — Done, no code. A
                         `.spec-table` (Spec/Value rows) of real GB10 specs from hp.com, then a
                         5-point core argument grounded in Level 6-8's actual CPU bottlenecks
                         (Grounding DINO's 30-60s+ runtime, ~2-3fps video tracking) rather than a
                         generic "AI needs GPUs" pitch.
                         L10 Writeup: scaling to the HP ZGX Fury AI Station — Done, no code. Same
                         `.spec-table` pattern with real GB300 specs, framed as "one engineer's
                         tool becoming shared facility infrastructure" — the natural Nano-to-Fury
                         scaling path, closing with the on-prem/fixed-cost argument that's constant
                         across both.
                         Shared template (all ten pages): eyebrow/h1/dek header with a
                         `.level-status` pill (currently all `.done`/green — `.priority` blue,
                         `.optional` ink-faint, `.goal` amber, and `.pending` ink-faint variants
                         still exist in the CSS but are unused now that every level is filled in;
                         leave them defined in case a future level needs a non-Done status again),
                         an "Approach" `.panel-title`/`.panel-desc`/`.panel-body` writeup, a
                         `.code-block` (dark `#0a0a0f` background, monospace, matches the
                         `.slides-embed`/`.app-embed` dark-iframe visual language used elsewhere
                         under /hp) for real code snippets — plus a `.code-block.terminal` variant
                         (green `#7ee787` text instead of gray, labeled with a small
                         `.output-label` above it reading "Terminal output") for genuinely captured
                         console output on Levels 1-6, see above — `.level-image`/`.image-pair`
                         figures — almost always a "Before" (original, unannotated) paired with an
                         "After" (detection result), each with a genuine, specific figcaption, never
                         a generic "detection result" caption — a `.video-embed` component (same
                         dark iframe pattern; Levels 7 and 8 both use it live in a shared
                         `.video-grid`, sized large per Avi's request — see above), a `.result-list`
                         (dot-bullet, same pattern as hp/30-60-90's `.plan-list`) for iteration
                         histories and built-feature lists, `.balance-note` for the "honest
                         limitation" callouts every level in this project deliberately includes,
                         and — only where something is genuinely still missing (L2's image
                         mismatch, L3's aerial demo image, L7/L8's oversized videos) — a
                         `.confirm-box` with plain prose (no more dashed `.confirm-blank` lines;
                         that pattern was for pure placeholders and no longer fits now that most
                         content is real). All of this CSS is duplicated per page as usual (no
                         shared stylesheet in this repo).
agents/index.html       URL: /agents — "Cleanie's Homebase." Added 2026-09-19. A standalone,
                         whimsical visual — NOT part of the light-editorial system or the /hp
                         sidebar, its own one-off "video-game screenshot" design system. Not
                         linked from the main nav (like tracker.html) — direct-URL-only, purely
                         personal/fun rather than portfolio content. Renders an isometric
                         RTS-style scene (StarCraft-esque camera angle, game HUD chrome —
                         nameplate with a health bar, corner brackets, minimap) of "Cleanie," a
                         LOTR-flavored armored cleanup golem (representing the real
                         CleanupComputer project) standing on a grassy plateau beside a
                         glowing-rune stone monolith (stands in for "the computer" it cleans).
                         Fog-of-war darkens the map's edges deliberately, so there's visual room
                         for more agents later WITHOUT any literal placeholder plots/islands in
                         the scene itself — Avi explicitly asked for no placeholders, only
                         Cleanie. Design tokens (all scoped to this page only, do not reuse
                         elsewhere): --sky-top/--sky-mid/--sky-horizon (stormy dusk gradient),
                         --grass/--grass-light/--grass-dark, --stone/--stone-light/--stone-dark,
                         --iron/--iron-light/--iron-dark (Cleanie's armor), --rune/--rune-dark
                         (glowing green magic-tech accent — used for the monolith's screen/cracks,
                         Cleanie's visor and chest sigil, and HUD status bar), --gold (HUD corner
                         brackets, belt buckle), --cloak/--cloak-dark, --leather, --wood-dark (the
                         hammer-mop haft). Fonts: Cinzel (engraved fantasy serif, nameplate/caption
                         heading) + Rajdhani (condensed HUD/UI sans) — different from every other
                         page's font stack in this repo, intentional. Single-theme by design (a
                         fixed in-game screenshot look, not meant to adapt to light mode) — do not
                         add a light-mode variant. Scene is hand-drawn inline SVG (viewBox 1280x720,
                         16:9 to read as a real game screenshot), no canvas/WebGL, no JS beyond
                         none currently (fully static). Carries the standard GA4 snippet + self-
                         exclusion block per the Analytics section below, but WITHOUT the
                         `content_group: 'HP Portfolio'` param since it isn't under hp/. This page
                         is explicitly a living/expanding piece — Avi plans to add more agents
                         (each presumably its own unit + plot on the same map) later; when that
                         happens, keep the same iso-plateau/HUD visual language and fog-of-war
                         framing rather than introducing a new visual system, and update this
                         entry plus README.md's page table together, same as any other new page.
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

As of 2026-08-22, every page under `hp/` (`index.html`, `case-study/index.html`, `use-cases/index.html`, `youtube/index.html`, `ai-research/index.html`, `p66-example/index.html` as of 2026-08-23, `30-60-90/index.html` as of 2026-08-27, and `object-detect-summary/index.html` plus `object-detect-level-1/index.html` through `object-detect-level-10/index.html` (ten levels, expanded from six on 2026-09-21) as of 2026-09-20 — eighteen pages total) shares one persistent left sidebar nav (`.hp-shell` / `.hp-sidenav` / `.hp-main` etc. — the CSS block is duplicated verbatim into each page's `<style>`, since there's no build step to share it from one file). This sidebar is deliberately its own design layer, sitting *outside* the light-editorial system every `/hp` page's content area now uses (see above): a dark (`#14161b`) fixed-left sidebar (220px, tightened from 232px on 2026-09-21 — see below) with the HP brand blue (`#0096D6`, defined as `--hp-blue` in every `/hp` page's own `:root` as of 2026-08-26, and always referenced as `var(--hp-blue, #0096D6)` with the hardcoded fallback kept for safety) as the active-link/accent color. This is the only place `--hp-blue` is used — the content area of every `/hp` page uses `--blue` (#1967b1) like `index.html`/`projects.html` instead; `hp/youtube/index.html` briefly leaked `--hp-blue` into its content-area "now playing"/"Featured" styling and was fixed back to `--blue` on 2026-08-26 to keep this rule true everywhere. The main link list, in order, all flat/same-level (six total): "Home - Job Fit" (`/hp` — relabeled from plain "Home" on 2026-08-23 so the sidebar itself hints at what that page is), ZGX Nano Case Study (`/hp/case-study`), Use Cases (`/hp/use-cases`), Youtube (`/hp/youtube`), AI Research (`/hp/ai-research`), P66 Example (`/hp/p66-example`). As of 2026-08-27, a second, visually separated group sits below that flat list: a `.hp-nav-section` div (top border + `.hp-nav-section-label` uppercase "Post Interview" label, both dark-sidebar-only styles, no `--blue`/`--hp-blue` conflict since they're just gray) wrapping its own `.hp-sidenav-links` nav with one link, "30/60/90 Plan" (`/hp/30-60-90`). As of 2026-09-20, a third such group sits below that one: `.hp-nav-section-label` "Object Detect", with "Summary" as a normal `.hp-nav-link` and Levels 1-10 as a compact 5-column numbered grid (see below), not eleven stacked links. Started at six levels on 2026-09-20, expanded to ten on 2026-09-21 — Levels 7-10 are pure `.panel-empty`/`.empty-tag` placeholders (same "Content Coming Soon" pattern the whole section started from) with a neutral `.level-status.pending` "TBD" pill, since Avi hasn't defined what those levels are yet; don't invent content for them. Sections stack in the order they were added — Post Interview, then Object Detect — each its own `.hp-nav-section` block, not nested inside one another. If Avi asks for more pages within an existing group (post-interview or object-detect), add them as more links inside that group's own `.hp-nav-section` block, not as new top-level flat items or a new group; only start a new `.hp-nav-section` when he explicitly asks for a new, differently-named group. Copy the `.hp-nav-section`/`.hp-nav-section-label` CSS (added right after `.hp-nav-link.active` in every page's shared nav CSS block) and the section HTML (right before `</aside>`) to all eighteen pages together, same as any other nav change. Deliberately **no** link back to the main site (`/`) — Avi removed it on 2026-08-22 so the sidebar doesn't distract a reader who's evaluating this HP-specific material. Don't re-add one unless he asks.

Every `/hp` page's `.wrap` uses the same `max-width: 1180px; margin: 0 auto; padding: 0 24px;` as of 2026-08-23 (matching `index.html`/`projects.html`) — before that, the four pages had drifted to three different widths (1100px, 1180px, 900px) as they were built one at a time. `h1` is `32px` / `line-height: 1.15` and `.dek` is `15.5px` / `max-width: 620px` on every `/hp` page too, for the same reason. `hp/use-cases/index.html`'s prose content is wrapped in a `.panel-body { max-width: 780px; }` div (matching `hp/case-study/index.html`'s existing convention) so its paragraphs don't stretch edge-to-edge now that `.wrap` is wider — the `industry-nav` chip grid and `balance-note` are inside that same wrapper. If you touch any `/hp` page's header typography or `.wrap`, check the other seventeen match.

**Tightened spacing (2026-09-21).** Avi asked for the sidebar to fit all 10 Object Detect levels without scrolling, so the whole nav got denser: `.hp-sidenav` padding `26px 18px` → `18px 14px`, width `232px` → `220px` (and `.hp-main`'s `margin-left` to match); `.hp-sidenav-head` margin-bottom `26px` → `14px`; `.hp-brand` `14.5px` → `13px`; `.hp-sidenav-links` gap `2px` → `1px`; `.hp-nav-link` padding `10px 12px` → `5px 8px` and font-size `13px` → `12px`; `.hp-nav-section` margin-top/padding-top `20px`/`16px` → `10px`/`8px`; `.hp-nav-section-label` margin-bottom `8px` → `4px`. On top of that, the Object Detect group's 10 level links no longer stack one-per-line — they're a `.hp-level-grid` (`display: grid; grid-template-columns: repeat(5, 1fr); gap: 3px`) of `.hp-level-link` cells showing just the number (`1`–`10`, with a `title="Level N"` tooltip for the number-only label), styled like `.hp-nav-link` but centered and smaller (`11px`, `5px 0` padding). "Summary" stays a normal full-width `.hp-nav-link` above the grid, in its own `<nav class="hp-sidenav-links">`, with the grid as a second `<nav class="hp-level-grid">` in the same `.hp-nav-section`. This grid pattern is specific to the Object Detect section (any group with many similarly-short items could reuse it) — the flat top-level list and "Post Interview" still use plain stacked `.hp-nav-link`s. All of this CSS/HTML is duplicated verbatim across all eighteen pages as usual; if you add an eleventh Object Detect level, extend the grid (still 5 columns, now 3 rows) rather than reverting to a stacked list.

Mobile (`max-width: 880px`): the sidebar becomes an off-canvas drawer (`transform: translateX(-100%)` by default, `.open` slides it in), triggered by a sticky "Menu" hamburger button (`#hpNavOpen`) that appears at the top of `.hp-main`, with a dark scrim (`#hpNavScrim`) behind it and a close button (`#hpNavClose`) in the drawer header. The toggle JS is a small inline `<script>` block at the end of each page's `<body>`, using those three element IDs plus `#hpSidenav` — keep the IDs consistent if you copy this block to a new `/hp` page.

If you add another `/hp` page to the main flat list, copy the entire `.hp-shell`/`.hp-sidenav`/etc. CSS block and the matching HTML structure + toggle `<script>` from `hp/ai-research/index.html` or `hp/p66-example/index.html` (the simplest pages), add a new `<a class="hp-nav-link">` row to the flat nav list on **all** `/hp` pages (including the new one, marked `active`), and use an absolute path (`/hp/whatever`) for its URL and for any cross-page links, since these pages live at different folder depths. If instead it belongs inside an existing group ("Post Interview" or "Object Detect"), add it inside that group's `.hp-nav-section` block instead (see above) — same rule about absolute paths and updating all eighteen pages' nav together.

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

## Analytics

As of 2026-09-13, every page in this repo carries the same Google Analytics 4 (gtag.js) snippet, pasted verbatim right after the opening `<head>` tag, Measurement ID `G-JVHGKBB8PD`:

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-JVHGKBB8PD"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-JVHGKBB8PD');
</script>
```

There's no shared layout/build step in this repo, so the snippet is duplicated into all 24 HTML files individually rather than living in one place: `index.html`, `projects.html`, `tracker.html`, `agents/index.html`, `hp-pmm-worksheet.html`, `zgx-nano-case-study.html`, and every `hp/*/index.html` page (eighteen of them). **Any new page added to this repo must get this same snippet pasted after its `<head>` tag** — it's easy to forget since there's no template enforcing it. One Measurement ID covers the whole `avikravi.github.io` domain, so nothing else needs to change if a new page is added elsewhere on the site.

Every page under `hp/` (all 18: `index.html`, `case-study/index.html`, `use-cases/index.html`, `youtube/index.html`, `ai-research/index.html`, `p66-example/index.html`, `30-60-90/index.html`, `object-detect-summary/index.html`, `object-detect-level-1/index.html` through `object-detect-level-10/index.html`) passes an extra `content_group: 'HP Portfolio'` parameter in its `gtag('config', ...)` call — a deliberate deviation from the plain snippet used elsewhere, added 2026-09-13 so Avi can filter GA4 reports (Engagement > Pages and screens, Path exploration) down to just visitors exploring the HP portfolio, separate from the rest of the site. Each page already has a distinct `<title>`, which combined with `content_group` is what makes per-page dwell time, click-through paths, and unique-visitor counts within `/hp` reportable in GA4 without any further code — this needs no additional event tracking, since GA4's default collection already measures page views, per-page engagement time, and users automatically on every full-page navigation. If a new `hp/` page is added, its `gtag('config', ...)` call must include this same `content_group` parameter — copy the pattern from any existing `hp/*/index.html` file.

### Self-exclusion (keep Avi's own visits out of the numbers)

As of 2026-09-13 (13 files as of 2026-09-19's `/agents` addition, 20 files as of 2026-09-20's five new `/hp/object-detect-level-*` pages, 24 files as of 2026-09-21's four more `/hp/object-detect-level-7` through `-10` placeholder pages), every one of them has a small inline script *immediately before* the gtag.js `<script>` tag (order matters — Google's disable flag must be set before the tag library loads):

```html
<!-- Google Analytics self-exclusion (must run before the tag below) -->
<script>
  (function () {
    try {
      var params = new URLSearchParams(window.location.search);
      if (params.get('ga_optout') === '1') {
        localStorage.setItem('ga_opt_out', 'true');
      } else if (params.get('ga_optout') === '0') {
        localStorage.removeItem('ga_opt_out');
      }
      if (localStorage.getItem('ga_opt_out') === 'true') {
        window['ga-disable-G-JVHGKBB8PD'] = true;
      }
    } catch (e) {}
  })();
</script>
```

This uses GA4/gtag.js's own documented opt-out mechanism (`window['ga-disable-<MEASUREMENT_ID>'] = true`). Avi opts out once per browser by visiting any page on the site with `?ga_optout=1` appended (e.g. `https://avikravi.github.io/?ga_optout=1`) — that sets a `localStorage` flag under the `avikravi.github.io` origin, which every other page on the site checks on load, so the opt-out follows him across all 24 pages without needing to repeat it per page. `?ga_optout=0` on any page clears the flag again (e.g. for testing that tracking is actually live). Caveats worth knowing: this is per-browser-profile, not per-computer — a different browser, a different OS user profile, or an incognito/private window won't inherit the flag and will still be tracked unless opted out separately in each; clearing site data/localStorage for `avikravi.github.io` also resets it. This client-side flag must stay in every page's `<head>`, ahead of the gtag.js script tag specifically (not just anywhere in `<head>`) — if a new page is ever added, copy this whole block plus the GA snippet from any existing page, in that order.

### Custom events for cross-origin embeds

Added 2026-09-14. GA4's automatic page-view/engagement tracking can't see *inside* a cross-origin `<iframe>` (no DOM access), which is a blind spot for the `/hp` pages that embed interactive content rather than just linking out. Manual `gtag('event', ...)` calls fill that gap:

- `hp/youtube/index.html`'s `playVideo(card)` function fires a `video_select` event (`video_title`, `video_type`, `video_id`) on every real click — it's only ever invoked from a click handler (never called on initial page load), so every event genuinely represents a visitor choosing a video, not the default-active P66 card firing on load.
- `hp/ai-research/index.html`'s and `hp/p66-example/index.html`'s embedded `<iframe>` (both `loading="lazy"`) fire an `embed_viewed` event (`embed_name`) on `onload` — since they're lazy-loaded, this only fires once the visitor actually scrolls the embed into view, not on page load, so it's a real signal they saw the interactive content and not just landed on the page.
- The "open in its own tab" fallback links on both those pages fire `embed_open_new_tab` (`embed_name`) on click; `p66-example`'s GitHub source link fires `p66_github_click`.
- `hp/object-detect-level-7/index.html`'s five YouTube `<iframe>`s (added 2026-09-21, also `loading="lazy"`) each fire their own `embed_viewed` event with a distinct `embed_name` (`level7_clip_1` through `level7_clip_5`) on `onload`, same reasoning as the ai-research/p66-example embeds. No "open in new tab" link for these — YouTube's own player chrome already offers that.

All of these guard with `typeof gtag === 'function'` before calling it, matching the defensive style of the self-exclusion snippet above. If a future `/hp` page embeds another cross-origin iframe or interactive widget, follow this same pattern (an `embed_viewed` on lazy `onload`, plus click events on any explicit follow-through links) rather than leaving it untracked.

## Conventions

- No sudo/admin needed for anything in this repo.
- Avi is on Windows (PowerShell), so prefer PowerShell-compatible instructions when giving him commands to run himself, though Claude Code's own tool calls handle git/file operations directly.
- Git author identity is `Avi Ravishankar <avikravi@gmail.com>` — already configured locally; don't reconfigure without being asked.
- Line endings: this repo is edited from both Windows and other environments; expect harmless LF→CRLF warnings from git on Windows — these are not errors.
- Keep commits scoped and the commit message descriptive of the actual content change (e.g. "Add application: Rivian", not "update").
- **Never mention compensation, salary, or pay figures anywhere on the site.** As of 2026-08-27, Avi explicitly asked that no page ever reference a dollar comp figure — this came up because a chat reply (not any page) mentioned a target salary number, and he wants the whole public site to stay silent on compensation entirely, not just the page that prompted it. If asked to discuss comp in future work, do it in chat only, never in a file that gets published.

## Keeping this file updated

When you make a structural change to this repo — a new page, a new data schema field, a new script, a change to the design tokens, a new top-level convention — update the relevant section of this file and `README.md` as part of that same commit. Don't wait to be asked. If you're unsure whether a change is "structural" enough to warrant a doc update, err toward updating.
