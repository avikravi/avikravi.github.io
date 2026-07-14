# CLAUDE.md

This file is read automatically by Claude Code at the start of every session in this repo. Keep it accurate — see "Keeping this file updated" at the bottom.

## What this repo is

Avi Ravishankar's personal site, hosted on GitHub Pages at `avikravi.github.io`. Plain HTML/CSS/JS, no build step, no framework, no npm dependencies for the deployed site itself.

## Files

```
index.html              Home page (bio, experience, skills)
projects.html           Project showcase
tracker.html            Live application tracker (reads tracker-data/applications.json)
tracker-data/
  applications.json     The tracker's actual data — see schema below
scripts/
  add_application.py    CLI helper to append a new application entry
master_resume_data.json Source-of-truth for Avi's real resume content (see below)
README.md               Human-facing docs
CLAUDE.md               This file
```

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
- Fixed nav bar with blurred background, gradient logo text, uppercase nav links, pink "active" state, gradient "Download Resume" button
- Animated grid background (`body::before`) + radial gradient overlay (`body::after`)
- Section headers: gradient `h2` (pink → blue), `.section-subtitle` in `--text-dim`
- Cards: `rgba(26,26,46,0.6)` background, 2px border in a low-opacity accent color, `border-radius: 16px`, `backdrop-filter: blur(10px)`

If asked to add a new page, copy the nav/header/footer markup and CSS variables from `tracker.html` or `index.html` rather than inventing new tokens.

**Every page's nav must stay in sync.** If you add/rename/remove a nav link on one page, update it on all three.

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

**Never invent or embellish a metric, title, or date in this file or in any resume generated from it.** If something is uncertain, add it to the file's `unresolved_conflicts_for_avi_to_confirm` array instead of guessing. Check that array before treating any entry as fully settled.

The `formatting_preferences` field in this JSON documents that Avi wants his existing resume .docx formatting (fonts, margins, spacing) preserved exactly — tailored resumes should be produced by editing a copy of his real .docx in place (unzip → edit `word/document.xml` → rezip), not by generating a new document from scratch.

## Conventions

- No sudo/admin needed for anything in this repo.
- Avi is on Windows (PowerShell), so prefer PowerShell-compatible instructions when giving him commands to run himself, though Claude Code's own tool calls handle git/file operations directly.
- Git author identity is `Avi Ravishankar <avikravi@gmail.com>` — already configured locally; don't reconfigure without being asked.
- Line endings: this repo is edited from both Windows and other environments; expect harmless LF→CRLF warnings from git on Windows — these are not errors.
- Keep commits scoped and the commit message descriptive of the actual content change (e.g. "Add application: Rivian", not "update").

## Keeping this file updated

When you make a structural change to this repo — a new page, a new data schema field, a new script, a change to the design tokens, a new top-level convention — update the relevant section of this file and `README.md` as part of that same commit. Don't wait to be asked. If you're unsure whether a change is "structural" enough to warrant a doc update, err toward updating.
