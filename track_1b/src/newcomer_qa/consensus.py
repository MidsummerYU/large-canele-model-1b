import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from pydantic import BaseModel

from newcomer_qa.config import Settings
from newcomer_qa.review import load_candidates

DECISIONS = ("keep", "edit", "drop")


class Review(BaseModel):
    candidate_id: str
    decision: str
    question: str = ""
    answer: str = ""
    variants: str = ""
    note: str = ""
    reason: str = ""


class Consensus(BaseModel):
    candidate_id: str
    votes: dict[str, str]
    outcome: str


def load_reviews(path: Path) -> dict[str, Review]:
    with path.open(encoding="utf-8") as f:
        return {r.candidate_id: r for r in (Review.model_validate_json(line) for line in f if line.strip())}


def load_reviewers(settings: Settings) -> dict[str, dict[str, Review]]:
    reviewers = {settings.first_pass_reviewer: load_reviews(settings.review_suggestions)}
    for path in sorted(settings.reviews_dir.glob("*_chunk_*.jsonl")):
        reviewers.setdefault(path.name.split("_chunk_")[0], {}).update(load_reviews(path))
    return reviewers


def outcome(decisions: list[str]) -> str:
    counts = Counter(decisions)
    if counts["keep"] == len(decisions):
        return "keep"
    if counts["drop"] * 2 > len(decisions):
        return "drop"
    return "adjudicate"


def fleiss_kappa(ratings: list[list[str]]) -> float:
    raters = len(ratings[0])
    counts = [Counter(item) for item in ratings]
    shares = [sum(c[d] for c in counts) / (len(ratings) * raters) for d in DECISIONS]
    observed = sum((sum(n * n for n in c.values()) - raters) / (raters * (raters - 1)) for c in counts) / len(ratings)
    expected = sum(p * p for p in shares)
    return (observed - expected) / (1 - expected)


def consensus(settings: Settings) -> None:
    candidates = load_candidates(settings)
    reviewers = load_reviewers(settings)
    for name, reviews in reviewers.items():
        missing = {c.candidate_id for c in candidates} - reviews.keys()
        if missing or any(r.decision not in DECISIONS for r in reviews.values()):
            raise ValueError(f"reviewer {name}: {len(missing)} items missing or an invalid decision")

    names = sorted(reviewers)
    results = [
        Consensus(candidate_id=c.candidate_id,
                  votes={n: reviewers[n][c.candidate_id].decision for n in names},
                  outcome=outcome([reviewers[n][c.candidate_id].decision for n in names]))
        for c in candidates
    ]
    settings.consensus.write_text("".join(r.model_dump_json() + "\n" for r in results), encoding="utf-8")

    ratings = [list(r.votes.values()) for r in results]
    print(f"{len(results)} items, reviewers: {', '.join(names)}")
    print(f"Fleiss' kappa (keep/edit/drop): {fleiss_kappa(ratings):.3f}")
    for a, b in combinations(names, 2):
        agree = sum(r.votes[a] == r.votes[b] for r in results) / len(results)
        print(f"  {a} vs {b}: {agree:.1%} same decision")
    print(f"outcomes: {dict(Counter(r.outcome for r in results))}")

    by_id = {c.candidate_id: c for c in candidates}
    with settings.adjudication_packet.open("w", encoding="utf-8") as f:
        for r in results:
            if r.outcome != "adjudicate":
                continue
            c = by_id[r.candidate_id]
            f.write(json.dumps({
                "candidate_id": c.candidate_id, "lang": c.lang, "question": c.question, "answer": c.answer,
                "variants": " | ".join(c.variants), "evidence": c.evidence_text,
                "reviews": {n: reviewers[n][c.candidate_id].model_dump(exclude={"candidate_id"}) for n in names},
            }, ensure_ascii=False) + "\n")
