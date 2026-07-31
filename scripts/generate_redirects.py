from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://shagiz-technologies.github.io"

REDIRECTS = {
    "televault/index.html": "/tele-vault/",
    "televault/privacy-policy.html": "/tele-vault/privacy-policy.html",
    "televault/privacy.html": "/tele-vault/privacy-policy.html",
    "tele-vault/privacy.html": "/tele-vault/privacy-policy.html",
    "tele-vault/privacy-policy/index.html": "/tele-vault/privacy-policy.html",
    "televault/terms.html": "/tele-vault/terms-of-service.html",
    "televault/terms-of-service.html": "/tele-vault/terms-of-service.html",
    "tele-vault/terms/index.html": "/tele-vault/terms-of-service.html",
    "televault/support.html": "/tele-vault/support.html",
    "televault/data-deletion.html": "/tele-vault/data-deletion.html",
    "tele-vault/delete-data.html": "/tele-vault/data-deletion.html",
    "privacy/televault.html": "/tele-vault/privacy-policy.html",
}

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <link rel="canonical" href="{canonical}">
  <meta http-equiv="refresh" content="0; url={target}">
  <link rel="stylesheet" href="/assets/css/site.css">
  <title>Page moved | Shagiz Technologies</title>
</head>
<body>
  <main id="main">
    <section class="hero">
      <div class="shell">
        <p class="eyebrow">Page moved</p>
        <h1>This page has a new address.</h1>
        <p class="lede">Continue to <a href="{target}">{canonical}</a>.</p>
      </div>
    </section>
  </main>
  <script>window.location.replace({target_json});</script>
</body>
</html>
"""


def quote_js(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> None:
    for relative_path, target in REDIRECTS.items():
        output = ROOT / relative_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            TEMPLATE.format(
                canonical=f"{ORIGIN}{target}",
                target=target,
                target_json=quote_js(target),
            ),
            encoding="utf-8",
            newline="\n",
        )


if __name__ == "__main__":
    main()
