import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor

import py3langid
from pydantic import BaseModel

from newcomer_qa.client import ChatRequest, RecordingClient
from newcomer_qa.config import Settings
from newcomer_qa.generate import Candidate

TRANSLATE_PROMPT = """Translate the question, the answer and the evidence below into English. \
Translate faithfully; do not correct or complete anything. Use exactly this format:

QUESTION: <English question>
ANSWER: <English answer>
EVIDENCE: <English evidence>

QUESTION: {question}
ANSWER: {answer}
EVIDENCE: {evidence}"""

TRANSLATION = re.compile(r"QUESTION:\s*(.+?)\s*ANSWER:\s*(.+?)\s*EVIDENCE:\s*(.+)", re.DOTALL)

REVIEW_COLUMNS = ["decision", "question_fixed", "answer_fixed", "variants_fixed", "note"]
SUGGESTION_FIELDS = ["decision", "question", "answer", "variants", "note", "reason"]


class English(BaseModel):
    question: str
    answer: str
    evidence: str


def load_candidates(settings: Settings) -> list[Candidate]:
    with settings.candidates.open(encoding="utf-8") as f:
        return [Candidate.model_validate_json(line) for line in f if line.strip()]


def load_suggestions(settings: Settings) -> dict[str, dict[str, str]]:
    if not settings.review_suggestions.exists():
        return {}
    with settings.review_suggestions.open(encoding="utf-8") as f:
        return {s["candidate_id"]: s for s in map(json.loads, filter(str.strip, f))}


def translate(client: RecordingClient, settings: Settings, candidate: Candidate, evidence: str) -> English | None:
    recording = client.chat(ChatRequest(
        model=settings.generator_model,
        messages=(("user", TRANSLATE_PROMPT.format(
            question=candidate.question, answer=candidate.answer, evidence=evidence)),),
        temperature=settings.generator_temperature,
        max_tokens=settings.generator_max_tokens,
    ))
    match = TRANSLATION.search(recording.content)
    return English(question=match[1], answer=match[2], evidence=match[3]) if match else None


def review_sheet(settings: Settings) -> None:
    candidates = load_candidates(settings)
    suggestions = load_suggestions(settings)
    client = RecordingClient(settings, settings.generation_recordings_dir, "live")

    def english(i: int) -> English | None:
        if candidates[i].lang not in settings.translate_for_review:
            return None
        return translate(client, settings, candidates[i], candidates[i].evidence_text)

    with ThreadPoolExecutor(settings.concurrency) as pool:
        translations = list(pool.map(english, range(len(candidates))))

    settings.review_sheet.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig: Excel on macOS only detects UTF-8 (accents, Chinese) when the file starts with a BOM.
    with settings.review_sheet.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "lang", "question_lang", "language_mismatch", "topic",
                         "question", "answer", "variants", "evidence",
                         "question_en", "answer_en", "evidence_en", "url",
                         *[f"suggested_{field}" for field in SUGGESTION_FIELDS], *REVIEW_COLUMNS])
        for candidate, en in zip(candidates, translations, strict=True):
            question_lang = py3langid.classify(candidate.question)[0]
            writer.writerow([
                candidate.candidate_id, candidate.lang, question_lang,
                "yes" if question_lang != candidate.lang else "", candidate.topic,
                candidate.question, candidate.answer, " | ".join(candidate.variants), candidate.evidence_text,
                en.question if en else "", en.answer if en else "", en.evidence if en else "",
                candidate.url,
                *[suggestions.get(candidate.candidate_id, {}).get(field, "") for field in SUGGESTION_FIELDS],
                *[""] * len(REVIEW_COLUMNS),
            ])
    missing = sum(1 for c, en in zip(candidates, translations) if c.lang in settings.translate_for_review and not en)
    print(f"{len(candidates)} rows written to {settings.review_sheet}, {missing} translations failed to parse")
