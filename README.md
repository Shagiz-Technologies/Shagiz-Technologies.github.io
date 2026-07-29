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

## Deployment blocker

`PRIVACY_CONTACT_EMAIL_REQUIRED` must be replaced with an approved, monitored
public privacy email before the TeleVault legal center is treated as
production-ready.
