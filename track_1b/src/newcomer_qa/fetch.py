import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import yaml
from pydantic import BaseModel

from newcomer_qa.chch import Page, parse_page
from newcomer_qa.config import Settings


class Sources(BaseModel):
    site: str
    languages: list[str]
    topics: dict[str, list[str]]


class StoredPage(BaseModel):
    page_id: str
    topic: str
    seed_path: str
    fetched_at: datetime
    page: Page


def load_sources(settings: Settings) -> Sources:
    return Sources.model_validate(yaml.safe_load(settings.sources.read_text(encoding="utf-8")))


def page_path(raw_dir: Path, lang: str, page_id: str) -> Path:
    return raw_dir / lang / f"{page_id}.json"


def load_pages(settings: Settings, lang: str) -> list[StoredPage]:
    return [StoredPage.model_validate_json(p.read_text(encoding="utf-8"))
            for p in sorted((settings.raw_dir / lang).glob("*.json"))]


class Fetcher:
    def __init__(self, settings: Settings):
        self._delay_s = settings.fetch_delay_s
        self._http = httpx.Client(
            headers={"User-Agent": settings.user_agent},
            timeout=settings.fetch_timeout_s,
            follow_redirects=True,
        )

    def page(self, url: str) -> Page:
        time.sleep(self._delay_s)
        response = self._http.get(url)
        response.raise_for_status()
        return parse_page(response.text, str(response.url))


def fetch(settings: Settings) -> None:
    sources = load_sources(settings)
    fetcher = Fetcher(settings)
    staging = settings.raw_dir.with_name(settings.raw_dir.name + ".partial")
    shutil.rmtree(staging, ignore_errors=True)
    page_ids: dict[str, str] = {}

    for topic, seed_paths in sources.topics.items():
        for seed_path in seed_paths:
            seed = fetcher.page(urljoin(sources.site, seed_path))
            # ch.ch files some pages under several German paths; the English URL identifies the page.
            key = seed.alternates.get("en", seed.url)
            if key in page_ids:
                print(f"{topic:<17} duplicate of {page_ids[key]}: {seed_path}")
                continue
            page_id = urlparse(key).path.rstrip("/").rsplit("/", 1)[-1]
            if page_id in page_ids.values():
                raise ValueError(f"page id {page_id} is used by two different pages")
            page_ids[key] = page_id

            others = [fetcher.page(url) for lang, url in seed.alternates.items()
                      if lang in sources.languages and lang != seed.lang]
            for page in [seed, *others]:
                stored = StoredPage(page_id=page_id, topic=topic, seed_path=seed_path,
                                    fetched_at=datetime.now(UTC), page=page)
                path = page_path(staging, page.lang, page_id)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(stored.model_dump_json(indent=1), encoding="utf-8")
                print(f"{topic:<17} {page.lang} {len(page.passages):>3} passages  {page_id}")

    shutil.rmtree(settings.raw_dir, ignore_errors=True)
    staging.rename(settings.raw_dir)
