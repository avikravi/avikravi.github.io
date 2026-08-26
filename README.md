# avikravi.github.io

Avi Ravishankar's personal site — portfolio, projects, and a live application tracker. Hosted on GitHub Pages, no build step, no framework.

**Live site:** https://avikravi.github.io

## Pages

| File | What it is |
|---|---|
| `index.html` | Home page — bio (computer vision research, product background), experience, skills |
| `projects.html` | Project showcase (TaskTag, Mesos, daytum, etc.) |
| `tracker.html` | Live job/PhD application tracker — see below. Deliberately **not linked from the nav bar**; only reachable if you know to type the URL. |

As of 2026-08-21, `index.html` and `projects.html` use a light-editorial design system (matching `hp/case-study/index.html` — see `CLAUDE.md` for the token reference), while `tracker.html` remains on the original neon dark design (its interactive UI would need separate rework to restyle safely). `index.html` and `projects.html` share a byte-for-byte identical nav bar, sourced from `index.html` — the only allowed difference between the two is which link carries the `active` class. Nav links: Home, Projects, Research (external — points to the dataset viewer in the separate `surgical-robotics-tissue-sim` repo, opens in a new tab), Download Resume. `tracker.html` keeps its own nav in the dark design system, with its own "Tracker" link (active), and is no longer expected to match the other two visually. If you edit the nav on `index.html` or `projects.html`, update the other of those two to match exactly.

## Application Tracker

`tracker.html` reads `tracker-data/applications.json` and renders it as a status board (Applied → Interviewing → Offer / Rejected / No Response) with search and industry filters.

### Adding an application

Fastest way — run the CLI helper from the repo root:

```bash
python scripts/add_application.py
```

Answer the prompts; it appends to `tracker-data/applications.json` and prints the git commands to publish it.

Or edit `tracker-data/applications.json` directly. Each entry:

```json
{
  "id": "rivian-a1b2c3",
  "company": "Rivian",
  "role": "Data Science Intern",
  "dateApplied": "2026-07-10",
  "status": "applied",
  "industry": "automotive",
  "location": "Irvine, CA",
  "link": "https://rivian.com/careers/...",
  "notes": "Tailored resume emphasizing Mesos hardware/UAV background"
}
```

`status` must be one of: `applied`, `interviewing`, `offer`, `rejected`, `ghosted`.

### Publishing changes

```bash
git add tracker-data/applications.json
git commit -m "Add application: <company>"
git push
```

GitHub Pages rebuilds automatically within a minute or two of a push to `master`.

## Resume Tailoring Tool

`tracker.html` also has a "Tailor a Resume" section (right below the page header, above the stats board): paste a company, role title, and job description, and it generates a matched `.docx` resume and cover letter, built entirely client-side from `master_resume_data.json`. A second "Check Match Score" button runs the same job description against your resume data and shows a 0–100 fit score without generating any documents.

How it works:
- `tailor/matching-engine.js` — tokenizes the job description and scores each `master_resume_data.json` experience entry by keyword overlap (industry tags count double), selecting the top 5 most relevant roles. Falls back to the 3 most recent roles if nothing scores. Includes the Black Swan Yoga entry only if the JD mentions a specific yoga/fitness-studio signal (narrowed from generic business terms like "sales" or "customer-facing", which showed up in unrelated technical JDs).
- `tailor/scoring-engine.js` — powers the "Check Match Score" button. Blends structured tag/skill overlap (reusing `matching-engine.js`'s scoring, weighted 70%) with raw text cosine similarity (weighted 30%) into a single 0–100 score, labeled Strong/Partial/Weak match. It's a keyword/text-similarity heuristic, not a reasoning model — the UI says so explicitly. Must load after `matching-engine.js` (reuses its `tokenize`/`scoreEntry`/`shouldIncludeBlackSwan`) and before `doc-builder.js`/`app.js`.
- `tailor/doc-builder.js` — builds the resume and cover letter as `docx.Document` objects from the selected entries, using the [docx](https://docx.js.org) library. Also skips any bullet whose text looks like leftover internal metadata (e.g. contains "NEEDS_", "PLACEHOLDER", "unresolved") as a second safety net beyond the `NEEDS_DETAIL`/`NEEDS_VERIFICATION` flag filter.
- `tailor/app.js` — wires both buttons: "Generate Resume & Cover Letter" calls into `doc-builder.js` and triggers both `.docx` downloads via `docx.Packer.toBlob`; "Check Match Score" calls `scoring-engine.js` and renders the score inline.

The `docx` library itself is loaded from a CDN (`<script>` tag in `tracker.html`'s `<head>`, pinned to `docx@8.5.0`) rather than bundled — no build step needed. It exposes a global `docx` object once loaded.

Nothing here calls a backend — all matching and document generation happens in the visitor's browser, and `master_resume_data.json` is fetched with a plain relative `fetch()` call, so this only works when the page is served over HTTP(S) (not opened directly as a `file://` URL).

## Local preview

No build step needed:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Resume data

`master_resume_data.json` (repo root) is the single source of truth for Avi's real work history, bullets, and metrics — used as input for generating tailored resumes per job application. It documents a handful of open conflicts between past resume versions (team sizes, dates, metric framing, etc.) in its own `unresolved_conflicts_for_avi_to_confirm` field — check that field before treating any entry it references as fully settled.

As of 2026-08-10, `AvinashResume2026.pdf` (repo root, linked from "Download Resume" on all three main pages) is the single, ultimate source of truth for both content and formatting — it replaced the previous two-PDF setup and the earlier `MASTERResume.docx` concept. No source `.docx` is currently on file for it.

## Unlisted / working pages: the `/hp` section

Not linked from the main nav bar, direct-URL-only. As of 2026-08-22, all of Avi's HP application material lives under `/hp`, sharing one persistent left sidebar nav (dark, HP-brand-blue accent, off-canvas/hamburger on mobile — see `CLAUDE.md`). As of 2026-08-23, every page's content area also shares the same light-editorial design tokens as `index.html`/`projects.html` (the worksheet used to have its own separate HP-blue look; it's now unified with the rest).

| URL | File | What it is |
|---|---|---|
| `/hp` | `hp/index.html` | **Home.** Static two-column job-fit table for a specific HP posting (Principal Technical Product Marketing Manager, AI Solutions) — one row per requirement, left column from the posting, right column ("How I Qualify") maintained directly by Claude Code as Avi describes his experience in chat. |
| `/hp/case-study` | `hp/case-study/index.html` | Working case study on the HP ZGX Nano AI Station — feedback/positive-review scraper boxes, personal research & interviews, and a competitor tracker. Originator of the light-editorial design system now also used by `index.html`/`projects.html`. The Use Cases tab that used to live here moved to its own page (below). |
| `/hp/use-cases` | `hp/use-cases/index.html` | 10-industry potential-use-case review for the ZGX Nano, split out from the case study into its own page. Industry-chip switcher UI (Energy first), each "Avi's review"/"HP's claim" shown as its own card. Cross-links back to the case study's "Box 1"/"Box 2" evidence it references. |
| `/hp/youtube` | `hp/youtube/index.html` | Youtube playlist of Avi's AI/ML project videos — a vertical "All Videos" list on the left (click an item to switch) and a big "now playing" player filling the rest of the row on the right. The video list (`hp/youtube/videos.json`) is manually maintained, not live-synced — see `CLAUDE.md` for why. As of 2026-08-25, the first three list items are hardcoded, non-YouTube Loom embeds — "P66 Vessel Integrity Intelligence" (tagged "Featured," active by default), "Teaching Robots Tissue Mechanics with ML," and "Card Database App" — inside the same list/player layout rather than a separate boxed section (an earlier boxed version was tried and rejected). Full order (5 videos total): P66 → Teaching Robots Tissue Mechanics with ML → Card Database App → Forecast 48 → Academic Paper Review. See `CLAUDE.md` for how to change it. |
| `/hp/ai-research` | `hp/ai-research/index.html` | Added 2026-08-23. Embeds Avi's summer 2026 Rice University surgical-robotics tissue-simulation research directly in-page via an iframe pointed at the live `surgical-robotics-tissue-sim` dataset viewer in a separate repo. |
| `/hp/p66-example` | `hp/p66-example/index.html` | Added 2026-08-23, sixth flat sidebar item. Embeds an independent pressure-vessel integrity prototype (ML corrosion prediction, fleet risk dashboard, ASME/API standards), live on Vercel at p66-vessel-integrity.vercel.app — synthetic data only, explicitly unaffiliated with Phillips 66 (a disclaimer the embedded app repeats in its own header). |

The old root-level `hp-pmm-worksheet.html` and `zgx-nano-case-study.html` are now thin meta-refresh redirect stubs pointing at `/hp` and `/hp/case-study`, in case any old links are still floating around.

## Working with Claude Code

This repo has a `CLAUDE.md` file with the design system, data schemas, and conventions Claude Code should follow automatically. Keep it updated when you add pages, change the schema, or change the design system — see the instructions inside `CLAUDE.md` itself.
