import argparse
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

from generate_redirects import ORIGIN, REDIRECTS


ROOT = Path(__file__).resolve().parents[1]
PRIMARY_PATHS = {
    "/": "index.html",
    "/tele-vault/": "tele-vault/index.html",
    "/tele-vault/privacy-policy.html": "tele-vault/privacy-policy.html",
    "/tele-vault/terms-of-service.html": "tele-vault/terms-of-service.html",
    "/tele-vault/support.html": "tele-vault/support.html",
    "/tele-vault/data-deletion.html": "tele-vault/data-deletion.html",
    "/tele-vault/security.html": "tele-vault/security.html",
}
TRACKER_PATTERNS = (
    "google-analytics",
    "googletagmanager",
    "facebook.com/tr",
    "connect.facebook.net",
    "segment.io",
    "mixpanel",
    "hotjar",
    "document.cookie",
    "localstorage",
    "sessionstorage",
)


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.ids: set[str] = set()
        self.lang: str | None = None
        self.title_count = 0
        self.h1_count = 0
        self.canonical: str | None = None
        self.refresh: str | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        values = dict(attrs)
        if tag == "html":
            self.lang = values.get("lang")
        if tag == "title":
            self.title_count += 1
        if tag == "h1":
            self.h1_count += 1
        if identifier := values.get("id"):
            self.ids.add(identifier)
        for attribute in ("href", "src"):
            if value := values.get(attribute):
                self.links.append((attribute, value))
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href")
        if (
            tag == "meta"
            and values.get("http-equiv", "").lower() == "refresh"
        ):
            self.refresh = values.get("content")


def route_to_file(route: str) -> Path:
    parsed = urlparse(route)
    path = unquote(parsed.path)
    if path == "/":
        return ROOT / "index.html"
    relative = path.lstrip("/")
    if path.endswith("/"):
        relative += "index.html"
    return ROOT / relative


def parse_documents() -> tuple[dict[Path, DocumentParser], list[str]]:
    documents: dict[Path, DocumentParser] = {}
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.html")):
        parser = DocumentParser()
        source = path.read_text(encoding="utf-8")
        try:
            parser.feed(source)
            parser.close()
        except Exception as error:
            errors.append(f"{path.relative_to(ROOT)}: invalid HTML: {error}")
            continue
        documents[path] = parser
        relative = path.relative_to(ROOT)
        if parser.lang != "en":
            errors.append(f"{relative}: expected html lang=\"en\"")
        if parser.title_count != 1:
            errors.append(f"{relative}: expected one title element")
        if parser.h1_count != 1:
            errors.append(f"{relative}: expected one h1, found {parser.h1_count}")
        lowered = source.lower()
        for pattern in TRACKER_PATTERNS:
            if pattern in lowered:
                errors.append(f"{relative}: prohibited tracker pattern {pattern}")
    return documents, errors


def validate_links(
    documents: dict[Path, DocumentParser],
) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    external: set[str] = set()
    for path, document in documents.items():
        relative = path.relative_to(ROOT)
        for _, raw_link in document.links:
            if raw_link.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            absolute = urljoin(f"{ORIGIN}/{relative.as_posix()}", raw_link)
            parsed = urlparse(absolute)
            if parsed.netloc == urlparse(ORIGIN).netloc:
                target = route_to_file(parsed.path)
                if not target.is_file():
                    errors.append(
                        f"{relative}: missing internal target {raw_link}",
                    )
                    continue
                if parsed.fragment:
                    target_document = documents.get(target)
                    if (
                        target_document is not None
                        and parsed.fragment not in target_document.ids
                    ):
                        errors.append(
                            f"{relative}: missing fragment #{parsed.fragment} "
                            f"in {target.relative_to(ROOT)}",
                        )
            elif parsed.scheme == "https":
                external.add(
                    f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    + (f"?{parsed.query}" if parsed.query else ""),
                )
            else:
                errors.append(f"{relative}: unexpected link scheme {raw_link}")
    return errors, external


def validate_canonicals(
    documents: dict[Path, DocumentParser],
) -> list[str]:
    errors: list[str] = []
    for route, relative_path in PRIMARY_PATHS.items():
        document = documents.get(ROOT / relative_path)
        expected = f"{ORIGIN}{route}"
        if document is None:
            errors.append(f"missing primary page {relative_path}")
        elif document.canonical != expected:
            errors.append(
                f"{relative_path}: canonical is {document.canonical!r}, "
                f"expected {expected!r}",
            )
    return errors


def validate_redirects(
    documents: dict[Path, DocumentParser],
) -> list[str]:
    errors: list[str] = []
    for relative_path, target in REDIRECTS.items():
        document = documents.get(ROOT / relative_path)
        if document is None:
            errors.append(f"missing redirect {relative_path}")
            continue
        expected_canonical = f"{ORIGIN}{target}"
        if document.canonical != expected_canonical:
            errors.append(f"{relative_path}: incorrect redirect canonical")
        refresh_target = re.search(
            r"url=(.+)$",
            document.refresh or "",
            flags=re.IGNORECASE,
        )
        if refresh_target is None or refresh_target.group(1).strip() != target:
            errors.append(f"{relative_path}: incorrect meta refresh target")
        if route_to_file(target).resolve() == (ROOT / relative_path).resolve():
            errors.append(f"{relative_path}: redirect loop")
    return errors


def validate_sitemap() -> list[str]:
    errors: list[str] = []
    sitemap = ROOT / "sitemap.xml"
    try:
        root = ET.parse(sitemap).getroot()
    except (OSError, ET.ParseError) as error:
        return [f"sitemap.xml: {error}"]
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = {node.text for node in root.findall("s:url/s:loc", namespace)}
    expected = {f"{ORIGIN}{route}" for route in PRIMARY_PATHS}
    missing = expected - locations
    if missing:
        errors.append(f"sitemap.xml: missing {sorted(missing)}")
    return errors


def relative_luminance(hex_color: str) -> float:
    channels = [
        int(hex_color[index : index + 2], 16) / 255
        for index in (1, 3, 5)
    ]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground: str, background: str) -> float:
    light, dark = sorted(
        [relative_luminance(foreground), relative_luminance(background)],
        reverse=True,
    )
    return (light + 0.05) / (dark + 0.05)


def validate_accessibility_css() -> list[str]:
    errors: list[str] = []
    css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8").lower()
    for requirement in (
        ":focus-visible",
        "@media (max-width: 720px)",
        "@media (prefers-reduced-motion: reduce)",
    ):
        if requirement not in css:
            errors.append(f"site.css: missing accessibility rule {requirement}")

    color_pairs = {
        "body text": ("#13251e", "#fffdf8"),
        "muted text": ("#5f6f67", "#fffdf8"),
        "primary button": ("#ffffff", "#147a50"),
        "footer text": ("#d8e4dd", "#13251e"),
    }
    for label, (foreground, background) in color_pairs.items():
        ratio = contrast_ratio(foreground, background)
        if ratio < 4.5:
            errors.append(
                f"site.css: {label} contrast {ratio:.2f}:1 is below 4.5:1",
            )
    return errors


def check_external_links(urls: set[str]) -> list[str]:
    errors: list[str] = []
    headers = {"User-Agent": "Shagiz-Technologies-site-validator/1.0"}
    for url in sorted(urls):
        last_error: Exception | None = None
        for attempt in range(3):
            request = urllib.request.Request(url, headers=headers, method="HEAD")
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    if response.status >= 400:
                        errors.append(
                            f"external link returned {response.status}: {url}",
                        )
                last_error = None
                break
            except urllib.error.HTTPError as error:
                if error.code not in {401, 403, 405, 429}:
                    errors.append(
                        f"external link returned {error.code}: {url}",
                    )
                last_error = None
                break
            except (urllib.error.URLError, TimeoutError) as error:
                last_error = error
                if attempt < 2:
                    time.sleep(attempt + 1)
        if last_error is not None:
            errors.append(f"external link failed: {url}: {last_error}")
    return errors


def main() -> int:
    arguments = argparse.ArgumentParser()
    arguments.add_argument(
        "--external",
        action="store_true",
        help="also perform network checks for external HTTPS links",
    )
    options = arguments.parse_args()

    documents, errors = parse_documents()
    link_errors, external = validate_links(documents)
    errors.extend(link_errors)
    errors.extend(validate_canonicals(documents))
    errors.extend(validate_redirects(documents))
    errors.extend(validate_sitemap())
    errors.extend(validate_accessibility_css())
    if options.external:
        errors.extend(check_external_links(external))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"Validated {len(documents)} HTML files, "
        f"{len(external)} external links, and {len(REDIRECTS)} redirects.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
