from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from newcomer_qa.config import Settings

# Packet file stem in data/raw/edge/ -> the tag the item gets in the metadata.
EDGE_KINDS = {"cantonal": "cantonal", "premise": "false_premise"}
EDGE_PREFIX = "edge-"
FACT_KIND = "fact"


class EdgeSource(BaseModel):
    """A ch.ch passage the drafter worked from; it stays local because it is page text."""

    model_config = ConfigDict(extra="ignore")

    source_id: str
    lang: str
    topic: str
    page_id: str
    url: str
    passage: str


class EdgeDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source_id: str
    decision: Literal["draft", "skip"]
    question: str = ""
    answer: str = ""
    variants: list[str] = []
    reason: str = ""


class EdgeReview(BaseModel):
    source_id: str
    kind: str
    decision: Literal["keep", "drop"]
    reason: str = ""


class EdgeCandidate(BaseModel):
    kind: str
    source: EdgeSource
    draft: EdgeDraft
    review: EdgeReview | None

    @property
    def item_id(self) -> str:
        return f"{EDGE_PREFIX}{self.kind}-{self.source.source_id}"

    @property
    def accepted(self) -> bool:
        return self.draft.decision == "draft" and self.review is not None and self.review.decision == "keep"


def _jsonl(path: Path, model) -> list:
    with path.open(encoding="utf-8") as f:
        return [model.model_validate_json(line) for line in f if line.strip()]


def load_edge_candidates(settings: Settings) -> list[EdgeCandidate]:
    """Every drafted edge case with its source passage and independent review, in packet order."""
    if not settings.edge_dir.exists():
        return []
    reviews = {(r.kind, r.source_id): r for r in _jsonl(settings.edge_dir / "review.jsonl", EdgeReview)}
    candidates = []
    for stem, kind in EDGE_KINDS.items():
        sources = _jsonl(settings.edge_dir / f"{stem}_packet.jsonl", EdgeSource)
        drafts = {d.source_id: d for d in _jsonl(settings.edge_dir / f"{stem}_drafts.jsonl", EdgeDraft)}
        candidates += [
            EdgeCandidate(kind=kind, source=s, draft=drafts[s.source_id], review=reviews.get((kind, s.source_id)))
            for s in sources
        ]
    return candidates
