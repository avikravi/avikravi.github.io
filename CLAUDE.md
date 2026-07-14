# CLAUDE.md

This file is read automatically by Claude Code at the start of every session in this repo. Keep it accurate — see "Keeping this file updated" at the bottom.

## What this repo is

Avi Ravishankar's personal site, hosted on GitHub Pages at `avikravi.github.io`. Plain HTML/CSS/JS, no build step, no framework, no npm dependencies for the deployed site itself.

## Files

```
index.html              Home page (bio, experience, skills)
projects.html           Project showcase
tracker.html            Live application tracker (reads tracker-data/applications.json)
                         Not linked from the nav bar on purpose — direct-URL-only.
tracker-data/
  applications.json     The tracker's actual data — see schema below
scripts/
  add_application.py    CLI helper to append a new application entry
AvinashResume.pdf        The resume actually linked from the "Download Resume" nav button
Avinash_Resume_2026.pdf  Fuller/more current resume (not linked from any page)
README.md               Human-facing docs
CLAUDE.md               This file
```

Note: there is no `master_resume_data.json` in this repo. If a future task references one, it doesn't exist yet — don't assume it does.

## Design system — DO NOT change without being asked

All three HTML pages use the same inline `<style>` tokens. Preserve these exactly when editing any page:

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

Shared conventions:
- Fixed nav bar with blurred background, gradient logo text ("AR"), uppercase nav links, pink "active" state, gradient "Download Resume" button (no icon — the arrow was removed)
- Animated grid background (`body::before`) + radial gradient overlay (`body::after`)
- Section headers: gradient `h2` (pink → blue), `.section-subtitle` in `--text-dim`
- Cards: `rgba(26,26,46,0.6)` background, 2px border in a low-opacity accent color, `border-radius: 16px`, `backdrop-filter: blur(10px)`

If asked to add a new page, copy the nav/header/footer markup and CSS variables from `tracker.html` or `index.html` rather than inventing new tokens.

**The nav bar must be byte-for-byte identical across all three pages — markup and CSS, including the mobile `@media (max-width: 768px)` breakpoint.** `index.html` is the source of truth. The only permitted difference is which link carries `class="active"`. Nav links (in order): Home, Projects, Research (external link, `target="_blank" rel="noopener"`, points to `avikravi.github.io/surgical-robotics-tissue-sim/dataset_viewer.html` — a separate repo, not a local page), Download Resume. `tracker.html` additionally carries its own "Tracker" link (active) after Research — that one link is the sole permitted addition, since `tracker.html` is deliberately not linked from the other two pages' nav. If you change one page's nav, copy the change to the other two verbatim.

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

## Resume files

`AvinashResume.pdf` is the one linked from the nav "Download Resume" button on all three pages — treat it as the live, public-facing resume. `Avinash_Resume_2026.pdf` is a fuller/more current version (includes the Computer Vision Research Intern role) that isn't linked anywhere yet.

**Never invent or embellish a metric, title, or date when writing resume content or site copy derived from it.** If Avi's actual work history needs to be pulled for a task (e.g. writing the About Me section), read it directly from these PDFs — there is no separate structured JSON source of truth in this repo.

## Conventions

- No sudo/admin needed for anything in this repo.
- Avi is on Windows (PowerShell), so prefer PowerShell-compatible instructions when giving him commands to run himself, though Claude Code's own tool calls handle git/file operations directly.
- Git author identity is `Avi Ravishankar <avikravi@gmail.com>` — already configured locally; don't reconfigure without being asked.
- Line endings: this repo is edited from both Windows and other environments; expect harmless LF→CRLF warnings from git on Windows — these are not errors.
- Keep commits scoped and the commit message descriptive of the actual content change (e.g. "Add application: Rivian", not "update").

## Keeping this file updated

When you make a structural change to this repo — a new page, a new data schema field, a new script, a change to the design tokens, a new top-level convention — update the relevant section of this file and `README.md` as part of that same commit. Don't wait to be asked. If you're unsure whether a change is "structural" enough to warrant a doc update, err toward updating.
