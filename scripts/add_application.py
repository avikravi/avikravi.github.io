#!/usr/bin/env python3
"""
Quick CLI to append a new job application to data/applications.json.

Usage:
    python scripts/add_application.py

Then answer the prompts. It appends to the JSON file and prints a reminder
to git add/commit/push.
"""
import json
import re
import uuid
from pathlib import Path
from datetime import date

DATA_PATH = Path(__file__).resolve().parent.parent / "tracker-data" / "applications.json"
VALID_STATUSES = ["applied", "interviewing", "offer", "rejected", "ghosted"]


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def prompt(label, default=None, choices=None):
    suffix = f" [{default}]" if default else ""
    while True:
        val = input(f"{label}{suffix}: ").strip()
        if not val and default is not None:
            val = default
        if choices and val not in choices:
            print(f"  Please choose one of: {', '.join(choices)}")
            continue
        if val or not choices:
            return val


def main():
    print("=== Add a new job application ===\n")

    company = prompt("Company")
    role = prompt("Role / title")
    date_applied = prompt("Date applied (YYYY-MM-DD)", default=date.today().isoformat())
    status = prompt("Status", default="applied", choices=VALID_STATUSES)
    industry = prompt("Industry (e.g. tech, automotive, sports, finance)")
    location = prompt("Location", default="Remote")
    link = prompt("Job listing URL (optional)", default="")
    notes = prompt("Notes (optional)", default="")

    entry = {
        "id": f"{slugify(company)}-{uuid.uuid4().hex[:6]}",
        "company": company,
        "role": role,
        "dateApplied": date_applied,
        "status": status,
        "industry": industry,
        "location": location,
        "link": link,
        "notes": notes,
    }

    if DATA_PATH.exists():
        data = json.loads(DATA_PATH.read_text())
    else:
        data = []

    # Drop the placeholder example entry automatically once real data exists
    data = [d for d in data if not d.get("isExample")]
    data.append(entry)

    DATA_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"\nAdded {company} — {role}.")
    print("Now run:")
    print("  git add tracker-data/applications.json")
    print(f'  git commit -m "Add application: {company}"')
    print("  git push")


if __name__ == "__main__":
    main()
