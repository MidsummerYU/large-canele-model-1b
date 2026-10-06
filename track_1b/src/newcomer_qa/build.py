import json
import re
from collections import Counter
from datetime import datetime

import py3langid
from pydantic import BaseModel

from newcomer_qa.config import Settings
from newcomer_qa.consensus import Consensus, Review, load_reviews
from newcomer_qa.fetch import StoredPage, page_path
from newcomer_qa.generate import Candidate
from newcomer_qa.review import load_candidates

WORD = re.compile(r"\w+")


class TestCase(BaseModel):
    item_id: str
    lang: str
    topic: str
    question: str
    answers: list[str]


class Metadata(BaseModel):
    item_id: str
    source_url: str
    source_modified_at: datetime | None
    # When the page was fetched, i.e. the date on which the answer was checked against ch.ch.
    source_fetched_at: datetime
    source_publisher: str
    license: str
    tags: list[str]
    drafted_by: str
    review_votes: dict[str, str]
    adjudicated: bool
    final_decision: str
    question_reworded: bool


class ReviewLogEntry(BaseModel):
    """One line per drafted candidate, kept or not; published so the path from draft to dataset can be audited."""

    candidate_id: str
    lang: str
    topic: str
    source_url: str
    review_votes: dict[str, str]
    consensus: str
    adjudication: str | None
    in_dataset: bool


def longest_copied_run(text: str, evidence: str) -> int:
    words, source = WORD.findall(text.casefold()), " ".join(WORD.findall(evidence.casefold()))
    best = 0
    for start in range(len(words)):
        for end in range(start + best + 1, len(words) + 1):
            if f" {' '.join(words[start:end])} " not in f" {source} ":
                break
            best = end - start
    return best


def final_review(candidate: Candidate, outcome: Consensus, adjudications: dict[str, Review]) -> Review | None:
    if outcome.outcome == "keep":
        return Review(candidate_id=candidate.candidate_id, decision="keep", question=candidate.question,
                      answer=candidate.answer, variants=" | ".join(candidate.variants))
    if outcome.outcome == "drop":
        return None
    review = adjudications[candidate.candidate_id]
    return review if review.decision != "drop" else None


def build_dataset(settings: Settings) -> None:
    candidates = load_candidates(settings)
    with settings.consensus.open(encoding="utf-8") as f:
        outcomes = {c.candidate_id: c for c in (Consensus.model_validate_json(line) for line in f if line.strip())}
    adjudications: dict[str, Review] = {}
    for path in sorted(settings.adjudications_dir.glob("result_*.jsonl")):
        adjudications.update(load_reviews(path))
    rewrites = {}
    if settings.question_rewrites.exists():
        with settings.question_rewrites.open(encoding="utf-8") as f:
            rewrites = {r["candidate_id"]: r["question"] for r in map(json.loads, filter(str.strip, f))}
    pending = [cid for cid, c in outcomes.items() if c.outcome == "adjudicate" and cid not in adjudications]
    if pending:
        raise ValueError(f"{len(pending)} items still need adjudication, e.g. {pending[0]}")

    fetched_at = {}
    for candidate in candidates:
        path = page_path(settings.raw_dir, candidate.lang, candidate.page_id)
        fetched_at[candidate.lang, candidate.page_id] = StoredPage.model_validate_json(path.read_text(encoding="utf-8")).fetched_at
    cases, metadata, log, problems = [], [], [], Counter()
    for candidate in candidates:
        outcome = outcomes[candidate.candidate_id]
        review = final_review(candidate, outcome, adjudications)
        adjudication = adjudications.get(candidate.candidate_id)
        log.append(ReviewLogEntry(
            candidate_id=candidate.candidate_id, lang=candidate.lang, topic=candidate.topic, source_url=candidate.url,
            review_votes=outcome.votes, consensus=outcome.outcome,
            adjudication=adjudication.decision if adjudication else None, in_dataset=review is not None,
        ))
        if review is None:
            continue
        question = rewrites.get(candidate.candidate_id, review.question)
        answers = [a for a in [review.answer, *review.variants.split("|")] if a.strip()]
        answers = list(dict.fromkeys(a.strip() for a in answers))
        if py3langid.classify(question)[0] != candidate.lang:
            problems["question language differs from the page"] += 1
        if longest_copied_run(question, candidate.evidence_text) >= settings.max_copied_words:
            problems[f"question copies {settings.max_copied_words}+ words from the source"] += 1
        cases.append(TestCase(item_id=candidate.candidate_id, lang=candidate.lang, topic=candidate.topic,
                              question=question, answers=answers))
        metadata.append(Metadata(
            item_id=candidate.candidate_id, source_url=candidate.url, source_modified_at=candidate.page_modified_at,
            source_fetched_at=fetched_at[candidate.lang, candidate.page_id],
            source_publisher=settings.source_publisher, license=settings.dataset_license,
            tags=[t.strip() for t in review.note.split(",") if t.strip()],
            drafted_by=candidate.generator_model, review_votes=outcome.votes,
            adjudicated=outcome.outcome == "adjudicate", final_decision=review.decision,
            question_reworded=candidate.candidate_id in rewrites,
        ))

    settings.dataset_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in (("test_cases.jsonl", cases), ("metadata.jsonl", metadata), ("review_log.jsonl", log)):
        (settings.dataset_dir / name).write_text(
            "".join(json.dumps(r.model_dump(mode="json"), ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"{len(cases)} test cases written to {settings.dataset_dir}")
    print(f"  by language: {dict(Counter(c.lang for c in cases))}")
    print(f"  by topic: {dict(Counter(c.topic for c in cases))}")
    print(f"  checks failed: {dict(problems) or 'none'}")
