# Security tests

Tests that keep the Kalshi credentials and private account data out of this **public** repo,
its **public** GitHub Actions logs, and the **public** dashboard. They run in the workflow
before the fetch step, so a failure stops the job before the secrets are ever used.

Run locally from the repo root:

```
python -m unittest discover -s kalshi/securitytests -v
```

Needs `requirements.txt` installed (the fetch tests generate a throwaway Ed25519 key with
`cryptography`). Git checks skip cleanly if git or `.git` is missing.

## What each file checks

| File | Protects against |
|---|---|
| `test_sec_repo_secrets.py` | Private keys, API key IDs (UUIDs), tokens or passwords in any tracked or not-yet-ignored file, or anywhere in git history; sensitive file names (`.env`, `*.pem`, `*.key`, `Kalshi-*.csv`, …) ever committed. Includes self-tests proving each detector catches a fake secret. |
| `test_sec_gitignore.py` | `.gitignore` missing rules for key files, `.env` files, Kalshi CSV exports and `.claude/settings.local.json`; or an over-broad rule hiding public files. |
| `test_sec_published_data.py` | `kalshi/data.json` (public) containing order/fill/account IDs, market tickers, UUIDs, emails or secret patterns. Plants fake identifiers to prove the checks fire. |
| `test_sec_fetch_no_leak.py` | `scripts/kalshi_fetch.py` printing the key ID, private key, request signature or a response body on HTTP errors, network errors, a malformed key, or missing secrets (run in-process and as a real subprocess); requests not going to Kalshi over HTTPS; any `print`/exit/log call in `scripts/kalshi_*.py` referencing credential-bearing values (AST check). |
| `test_sec_workflow.py` | Secrets used outside the fetch step or inlined into `run:`; risky triggers (`pull_request`, `push`, …); debug logging; `KALSHI_API_HOST` overridden; permissions wider than `contents: write`; tests not running before secrets; the bot committing anything other than `kalshi/data.json`. |
| `test_sec_page.py` | The dashboard calling Kalshi directly, fetching anything but `data.json`, storing credentials in the browser, or loading scripts over plain HTTP. |

Failures name the file, line and pattern, never the secret itself.

## Adding a test

- Add a new detector to `SECRET_PATTERNS` (or a file name to `SENSITIVE_NAME_PATTERNS`) in
  `sec_helpers.py`, plus a fake example in `SecretPatternSelfTests` so it is proven to fire.
- Never put a real or realistic secret in a test file. Build fakes at runtime by joining pieces
  (`"AKIA" + "ABCD…"`), so the repo-wide scan never flags the tests themselves.
- Never weaken a check to make it pass; fix the leak (and rotate the key if it was ever committed).

## If a test finds a real secret

1. Revoke/rotate it first (Kalshi → API keys; then update the GitHub repo secret).
2. Then remove it from the repo. Deleting it in a new commit is not enough: it stays in history.

## Ideas for later

- Pin GitHub Actions to commit SHAs instead of `@v7` tags.
- Subresource Integrity (`integrity=`) on the Chart.js `<script>` tag.
- Check the GitHub repo settings (secret scanning, push protection) via the API.
- Scan the CSV fallback's inputs and outputs the same way as `data.json`.
