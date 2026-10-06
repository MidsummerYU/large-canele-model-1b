import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from pydantic import BaseModel

from newcomer_qa.client import ChatRequest, RecordingClient
from newcomer_qa.config import Settings
from newcomer_qa.fetch import StoredPage, load_pages, load_sources

GENERATE_PROMPT = """You write test questions for a benchmark that checks what a language model knows about \
Swiss administrative procedures for people who have just moved to Switzerland.
Below are the numbered passages of one page of ch.ch, the official information portal of the Swiss authorities.

Write {n} questions. Each question must:
- be something a newcomer to Switzerland would really ask, phrased in your own words, not copied from the page;
- make sense on its own, without the page: name the procedure, permit or insurance it is about;
- have one short, factual answer that a single passage states explicitly: a deadline, an amount, an age, \
a number, an office, a document, or yes/no;
- have the same answer everywhere in Switzerland: skip facts that the passages say depend on the canton or commune.

Write the questions and answers in the same language as the passages. Use this format, one block per question:

QUESTION: <the question>
ANSWER: <the shortest complete correct answer>
VARIANTS: <other wordings of the same answer, separated by " | "; each one must be complete and correct on its own>
EVIDENCE: <number of the passage that states the answer>

{passages}"""

BLOCK_START = re.compile(r"^(?=QUESTION:)", re.MULTILINE)
FIELD = re.compile(r"^(QUESTION|ANSWER|VARIANTS|EVIDENCE):[ \t]*(.*?)\s*$", re.MULTILINE)
EVIDENCE = re.compile(r"\[?(\d+)\]?")


class Candidate(BaseModel):
    candidate_id: str
    lang: str
    topic: str
    page_id: str
    url: str
    page_modified_at: datetime | None
    question: str
    answer: str
    variants: list[str]
    evidence: int
    evidence_text: str
    generator_model: str


def question_count(page: StoredPage, settings: Settings) -> int:
    return min(settings.max_questions_per_page, max(1, len(page.page.passages) // settings.passages_per_question))


def numbered(page: StoredPage) -> str:
    return "\n\n".join(f"[{i}] {p.heading}\n{p.text}" for i, p in enumerate(page.page.passages, 1))


def parse_candidates(content: str, page: StoredPage, model: str) -> tuple[list[Candidate], Counter[str]]:
    candidates: list[Candidate] = []
    rejected: Counter[str] = Counter()
    for block in BLOCK_START.split(content):
        if not block.strip().startswith("QUESTION:"):
            continue
        fields = dict(FIELD.findall(block))
        evidence = EVIDENCE.fullmatch(fields.get("EVIDENCE", ""))
        if not fields.get("QUESTION") or not fields.get("ANSWER") or not evidence:
            rejected["malformed block"] += 1
            continue
        if not 1 <= int(evidence[1]) <= len(page.page.passages):
            rejected["evidence passage does not exist"] += 1
            continue
        candidates.append(Candidate(
            candidate_id=f"{page.page.lang}-{page.page_id}-{len(candidates) + 1:02d}",
            lang=page.page.lang,
            topic=page.topic,
            page_id=page.page_id,
            url=page.page.url,
            page_modified_at=page.page.modified_at,
            question=fields["QUESTION"],
            answer=fields["ANSWER"],
            variants=[v.strip() for v in fields.get("VARIANTS", "").split("|") if v.strip()],
            evidence=int(evidence[1]) - 1,
            evidence_text=page.page.passages[int(evidence[1]) - 1].text,
            generator_model=model,
        ))
    return candidates, rejected


def generate_for_page(
    client: RecordingClient, settings: Settings, page: StoredPage
) -> tuple[list[Candidate], Counter[str]]:
    prompt = GENERATE_PROMPT.format(n=question_count(page, settings), passages=numbered(page))
    recording = client.chat(ChatRequest(
        model=settings.generator_model,
        messages=(("user", prompt),),
        temperature=settings.generator_temperature,
        max_tokens=settings.generator_max_tokens,
    ))
    return parse_candidates(recording.content, page, settings.generator_model)


def generate(settings: Settings) -> None:
    sources = load_sources(settings)
    client = RecordingClient(settings, settings.generation_recordings_dir, "live")
    pages = [page for lang in sources.languages for page in load_pages(settings, lang)]
    with ThreadPoolExecutor(settings.concurrency) as pool:
        results = list(pool.map(lambda page: generate_for_page(client, settings, page), pages))

    candidates = [c for page_candidates, _ in results for c in page_candidates]
    settings.candidates.write_text("".join(c.model_dump_json() + "\n" for c in candidates), encoding="utf-8")
    rejected = sum((page_rejected for _, page_rejected in results), Counter())
    print(f"{len(candidates)} candidates from {len(pages)} pages; rejected: {dict(rejected) or 'none'}")
    for (lang, topic), count in sorted(Counter((c.lang, c.topic) for c in candidates).items()):
        print(f"  {lang} {topic:<17} {count}")
