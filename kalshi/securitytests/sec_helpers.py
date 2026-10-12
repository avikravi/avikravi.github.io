"""Shared helpers for the security tests in kalshi/securitytests/.

Paths, git access and the secret-detection patterns live here so every test
uses the same definitions. Patterns are written so that this file's own text
never matches them (a "[" or a split string breaks each one), which keeps the
repo-wide scan from flagging the scanner itself.
"""

import os
import re
import subprocess
import sys
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
KALSHI_DIR = os.path.dirname(TESTS_DIR)
REPO = os.path.dirname(KALSHI_DIR)
SCRIPTS = os.path.join(REPO, "scripts")
WORKFLOW = os.path.join(REPO, ".github", "workflows", "kalshi.yml")
DATA_JSON = os.path.join(KALSHI_DIR, "data.json")

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

# File types never scanned as text (images, fonts, model weights, PDFs).
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svgz", ".pdf", ".pt",
    ".mp4", ".mov", ".webm", ".woff", ".woff2", ".ttf", ".otf", ".zip", ".gz", ".pyc",
}

# Secret patterns: name -> compiled regex. Add new ones here; every scan uses them.
SECRET_PATTERNS = {
    "PEM private key block": re.compile("-----BEGIN " + r"[A-Z ]*PRIVATE KEY" + "-----"),
    "Kalshi key assigned a literal value": re.compile(
        r"KALSHI_(?:API_KEY_ID|PRIVATE_KEY)\s*[:=]\s*[\"']?(?![\"']?\$)[A-Za-z0-9+/=_-]{8,}"),
    "UUID (Kalshi API key IDs and order IDs are UUIDs)": re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "OpenAI / Anthropic key": re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{24,}"),
    "Slack token": re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"),
    "Password with a literal value": re.compile(
        r"(?i)\bpass(?:word|wd)\s*[:=]\s*[\"'][^\"'\s]{4,}[\"']"),
}

# File names that must never be committed (checked against tracked files and .gitignore).
SENSITIVE_NAME_PATTERNS = [
    re.compile(r"(^|/)\.env(\..+)?$"),
    re.compile(r"\.pem$"),
    re.compile(r"\.key$"),
    re.compile(r"\.p12$|\.pfx$"),
    re.compile(r"(^|/)id_(rsa|ed25519|ecdsa)$"),
    re.compile(r"(^|/)Kalshi-[^/]*\.csv$"),
    re.compile(r"(^|/)\.claude/settings\.local\.json$"),
]


def git(*args):
    """Run git in the repo and return stdout; raises SkipTest when git or .git is missing."""
    if not os.path.isdir(os.path.join(REPO, ".git")):
        raise unittest.SkipTest("not a git checkout")
    try:
        result = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", check=True)
    except FileNotFoundError:
        raise unittest.SkipTest("git is not installed")
    return result.stdout


def repo_files(include_untracked=True):
    """Tracked files plus untracked files that are NOT ignored (one `git add .` from public)."""
    names = git("ls-files", "-z").split("\0")
    if include_untracked:
        names += git("ls-files", "--others", "--exclude-standard", "-z").split("\0")
    return sorted({name for name in names if name})


def read_text(rel_path):
    """Return the file's text, or None for binary/unreadable files."""
    if os.path.splitext(rel_path)[1].lower() in BINARY_EXTENSIONS:
        return None
    full = os.path.join(REPO, rel_path)
    try:
        with open(full, "rb") as handle:
            raw = handle.read()
    except OSError:
        return None
    if b"\0" in raw[:8192]:
        return None
    return raw.decode("utf-8", errors="replace")


def find_secrets(text):
    """Return [(pattern name, line number)] for every secret-pattern hit. Never returns the match itself."""
    hits = []
    for name, pattern in SECRET_PATTERNS.items():
        for found in pattern.finditer(text):
            hits.append((name, text.count("\n", 0, found.start()) + 1))
    return hits
