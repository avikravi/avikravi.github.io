# avikravi.github.io

Avi Ravishankar's personal site — portfolio, projects, and a live application tracker. Hosted on GitHub Pages, no build step, no framework.

**Live site:** https://avikravi.github.io

## Pages

| File | What it is |
|---|---|
| `index.html` | Home page — bio (computer vision research, product background), experience, skills |
| `projects.html` | Project showcase (TaskTag, Mesos, daytum, etc.) |
| `tracker.html` | Live job/PhD application tracker — see below. Deliberately **not linked from the nav bar**; only reachable if you know to type the URL. |

All three share the same design system (CSS variables defined inline in each file's `<style>` block — see `CLAUDE.md` for the token reference) and a byte-for-byte identical nav bar, sourced from `index.html`. The only allowed difference between pages is which link carries the `active` class. Nav links: Home, Projects, Research (external — points to the dataset viewer in the separate `surgical-robotics-tissue-sim` repo, opens in a new tab), Download Resume. `tracker.html` additionally has its own "Tracker" link (active) that the other two pages don't carry. If you edit the nav on one page, update the other two to match exactly.

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

## Local preview

No build step needed:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Resume data

`master_resume_data.json` (repo root) is the single source of truth for Avi's real work history, bullets, and metrics — used as input for generating tailored resumes per job application. It documents a handful of open conflicts between past resume versions (team sizes, dates, metric framing, etc.) in its own `unresolved_conflicts_for_avi_to_confirm` field — check that field before treating any entry it references as fully settled.

Its `formatting_preferences` field names `MASTERResume.docx` as the canonical formatting template (matching the live `AvinashResume.pdf` linked from the site) — tailored resumes should be produced by editing a copy of that .docx in place, not by generating a new one from scratch.

Two resume PDFs also live at the repo root: `AvinashResume.pdf` (linked from the "Download Resume" button on all three pages) and `Avinash_Resume_2026.pdf` (a fuller/more current version, not currently linked from any page).

## Working with Claude Code

This repo has a `CLAUDE.md` file with the design system, data schemas, and conventions Claude Code should follow automatically. Keep it updated when you add pages, change the schema, or change the design system — see the instructions inside `CLAUDE.md` itself.
