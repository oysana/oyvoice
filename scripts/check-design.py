"""Validate the design roles and both localized entry points without dependencies."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json
import re

ROOT = Path(__file__).resolve().parent.parent
ROLES = {
    "bento": (2, 88),
    "editorial": (0, 155),
    "action": (1, 55),
    "faq": (0, 180),
}
VOID = set("area base br col embed hr img input link meta param source track wbr".split())


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.stack = []
        self.sections = {}
        self.ids = set()
        self.errors = []
        self.alternates = []
        self.assets = set()
        self.hero_headings = 0
        self.offer_metadata = False
        self.feed(path.read_text())
        self.close()

    def error(self, message):
        self.errors.append(f"{self.path.relative_to(ROOT)}:{self.getpos()[0]}: {message}")

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag not in VOID:
            self.stack.append((tag, attrs))
        if tag == "h1":
            self.hero_headings += 1
        if attrs.get("id"):
            if attrs["id"] in self.ids:
                self.error(f"repeated id {attrs['id']}")
            self.ids.add(attrs["id"])
        role = attrs.get("data-design-section")
        if "data-design-section" in attrs:
            if tag != "section" or role not in ROLES or role in self.sections:
                self.error(f"invalid or repeated section role: {role}")
                return
            self.sections[role] = {"label": attrs.get("aria-labelledby"), "h2": [], "visuals": 0, "actions": 0, "words": 0}
        current = self.current_section()
        if current:
            if tag == "h2":
                current["h2"].append(attrs.get("id"))
            if "data-design-visual" in attrs:
                if tag not in ("img", "picture", "div"):
                    self.error("visual markers belong on img, picture, or a canvas wrapper")
                current["visuals"] += 1
            if "data-design-primary" in attrs:
                if role or tag != "a" or attrs.get("href") != "https://github.com/oysana/oyvoice/issues":
                    self.error("the primary action must link to the public GitHub Issues")
                if (attrs.get("class") or "").split() != ["oy-button"]:
                    self.error("the primary action must use oy-button")
                current["actions"] += 1
            if tag == "img" and not {"alt", "width", "height", "src"} <= attrs.keys():
                self.error("every image needs dimensions and alt")
        if tag == "link" and attrs.get("rel") == "alternate":
            self.alternates.append((attrs.get("hreflang"), attrs.get("href")))
        if tag == "a" and attrs.get("hreflang"):
            self.check_asset(attrs.get("href", "") + "index.html")
        if tag in ("img", "source", "script", "link"):
            for key in ("src", "srcset", "href"):
                if value := attrs.get(key):
                    if attrs.get("rel") == "alternate":
                        continue
                    self.check_asset(value)

    def check_asset(self, value):
        if urlsplit(value).scheme or value.startswith("/"):
            self.error(f"asset must use a project-relative path: {value}")
            return
        path = (self.path.parent / value).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            self.error(f"missing asset {value}")
        self.assets.add(path)

    def current_section(self):
        for tag, attrs in reversed(self.stack):
            if tag == "section":
                return self.sections.get(attrs.get("data-design-section"))
        return None

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            self.error(f"unexpected closing {tag}")
            return
        self.stack.pop()

    def handle_data(self, data):
        if self.stack and self.stack[-1][1].get("type") == "application/ld+json":
            self.offer_metadata = "offers" in json.loads(data)
        if current := self.current_section():
            current["words"] += len(data.split())

    def verify(self):
        if self.stack:
            self.error("unclosed tags")
        if self.offer_metadata:
            self.error("structured pricing is not allowed while sales are closed")
        if self.hero_headings != 1 or list(self.sections) != list(ROLES):
            self.error("expected one h1 and bento, editorial, action, FAQ in that order")
        expected = {("en", "https://oysana.github.io/oyvoice/"), ("ru", "https://oysana.github.io/oyvoice/ru/")}
        if set(self.alternates) != expected:
            self.error("hreflang must resolve under the GitHub Pages project path")
        for role, entry in self.sections.items():
            visuals, words = ROLES[role]
            if not entry["label"] or entry["h2"] != [entry["label"]]:
                self.error(f"{role} requires one h2 referenced by aria-labelledby")
            if entry["visuals"] < visuals or entry["words"] > words:
                self.error(f"{role}: {entry['visuals']} visuals and {entry['words']} words, require ≥{visuals} visuals and ≤{words} words")
            if entry["actions"] != int(role == "action"):
                self.error(f"{role}: exactly one primary action belongs in the action section")
        return self.errors


def check_css():
    css = (ROOT / "assets/storefront.css").read_text()
    tokens = re.findall(r"(?m)^  (--[\w-]+):", css)
    scopes = set(re.findall(r"(?m)^\{?([^{}\n]+)\{\s*\n(?:\s*--[\w-]+:)", css))
    if any(scope.strip() != ".oy-story" for scope in scopes) or len(tokens) != len(set(tokens)):
        return ["assets/storefront.css: design tokens may only be set once, in .oy-story"]
    for name in ("tile-corner", "grid-gap", "tile-inset", "divider", "accent-action", "focus", "control-feedback"):
        if name not in {token[2:] for token in tokens} or f"var(--{name})" not in css:
            return [f"assets/storefront.css: missing or unused role token --{name}"]
    return []


errors = check_css()
for file in ("index.html", "ru/index.html"):
    errors.extend(Page(ROOT / file).verify())

if errors:
    raise SystemExit("\n".join(errors))
print("Design contract passed for EN and RU")
