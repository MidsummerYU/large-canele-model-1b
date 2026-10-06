import json
from collections.abc import Iterator
from datetime import datetime
from urllib.parse import urljoin

from pydantic import BaseModel
from selectolax.lexbor import LexborHTMLParser, LexborNode

HEADINGS = (
    '[data-component="title"]',
    '[data-component="subtitle"]',
    ".accordion-item > label > span:first-child",
)
BODIES = ('[data-component="lead"]', '[data-component="p"]', '[data-component="list"]')
# Widgets such as the canton picker ship every option in the HTML and hide all but the selected one.
HIDDEN = '[style*="display:none"], [style*="display: none"], [hidden]'


class Passage(BaseModel):
    heading: str
    text: str


class Page(BaseModel):
    url: str
    lang: str
    title: str
    modified_at: datetime | None
    passages: list[Passage]
    alternates: dict[str, str]


def _clean(node: LexborNode) -> str:
    return " ".join(node.text(deep=True).split())


def _is_link_list(node: LexborNode) -> bool:
    items = node.css("li")
    return bool(items) and all(
        (link := li.css_first("a")) is not None and _clean(link) == _clean(li) for li in items
    )


def _list_text(node: LexborNode) -> str:
    return "\n".join(text for li in node.css("li") if (text := _clean(li)))


def _blocks(tree: LexborHTMLParser) -> Iterator[tuple[str, bool, str]]:
    heading = ""
    for node in tree.css(", ".join(HEADINGS + BODIES)):
        if any(node.css_matches(selector) for selector in HEADINGS):
            heading = _clean(node)
            continue
        is_list = node.attributes.get("data-component") == "list"
        if is_list and _is_link_list(node):
            continue
        text = _list_text(node) if is_list else _clean(node)
        if text:
            yield heading, is_list, text


def _passages(tree: LexborHTMLParser) -> list[Passage]:
    passages: list[Passage] = []
    for heading, is_list, text in _blocks(tree):
        previous = passages[-1] if passages else None
        if is_list and previous and previous.heading == heading and previous.text.endswith(":"):
            previous.text += "\n" + text
        else:
            passages.append(Passage(heading=heading, text=text))
    return passages


def _modified_at(tree: LexborHTMLParser) -> datetime | None:
    for script in tree.css('script[type="application/ld+json"]'):
        data = json.loads(script.text())
        for item in data.get("@graph", [data]):
            if "dateModified" in item:
                return datetime.fromisoformat(item["dateModified"])
    return None


def _alternates(tree: LexborHTMLParser, url: str) -> dict[str, str]:
    alternates = {}
    for link in tree.css("a[href]"):
        lang = _clean(link).lower()
        if link.attributes["href"].startswith(f"/{lang}/"):
            alternates[lang] = urljoin(url, link.attributes["href"])
    return alternates


def parse_page(html: str, url: str) -> Page:
    tree = LexborHTMLParser(html)
    for node in tree.css(HIDDEN):
        node.decompose()
    title = tree.css_first('[data-component="title"]')
    return Page(
        url=url,
        lang=tree.css_first("html").attributes["lang"],
        title=_clean(title) if title else "",
        modified_at=_modified_at(tree),
        passages=_passages(tree),
        alternates=_alternates(tree, url),
    )
