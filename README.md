# Shagiz Technologies Website

Official organization website and consumer-facing legal documentation for
Shagiz Technologies products.

## Local preview

```bash
python -m http.server 8080
```

Open `http://localhost:8080/`.

## Validation

```bash
python scripts/validate_site.py
python scripts/validate_site.py --external
```

## Deployment

GitHub Pages deploys the repository root after changes reach `main`. Pull
requests run validation only and never deploy.

Canonical origin: <https://shagiz-technologies.github.io/>

## Privacy inquiries

The TeleVault Privacy Policy provides a public GitHub inquiry mechanism for
non-sensitive privacy and deletion-process questions. Credentials, personal
media, Telegram identifiers, databases, session material, metadata snapshots,
and Recovery Keys must never be posted publicly. Security vulnerabilities use
GitHub Private Vulnerability Reporting.
