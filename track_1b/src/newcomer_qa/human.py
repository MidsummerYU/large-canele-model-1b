import json
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pydantic import BaseModel

from newcomer_qa.client import ChatRequest, Mode, RecordingClient
from newcomer_qa.config import Settings
from newcomer_qa.evaluate import EvalConfig, Grade, Response, gold_target, load_test_cases

TRANSLATE_PROMPT = "Translate into English. Reply with the translation only.\n\n{text}"


class SampleItem(BaseModel):
    key: str
    lang: str
    question: str
    gold: str
    response: str
    translation: dict[str, str] | None


class HumanGrade(BaseModel):
    key: str
    grade: Grade


def response_key(response: Response) -> str:
    return f"{response.model}/{response.condition}/{response.item_id}"


def sample(responses: list[Response], share: float, seed: int) -> list[Response]:
    """A seeded random share of each model's judgements, so judges can draw the same sample."""
    rng = random.Random(seed)
    picked = []
    for model in sorted({r.model for r in responses}):
        rows = [r for r in responses if r.model == model]
        picked += rng.sample(rows, round(share * len(rows)))
    return picked


def load_responses(path: Path) -> list[Response]:
    with path.open(encoding="utf-8") as f:
        return [Response.model_validate_json(line) for line in f if line.strip()]


def write_human_page(settings: Settings, mode: Mode) -> Path:
    config = EvalConfig.load(settings.eval_config)
    client = RecordingClient(settings.model_copy(update={"llm_base_url": config.endpoint}), settings.recordings_dir, mode)
    cases = {c.item_id: c for c in load_test_cases(settings.dataset_dir / "test_cases.jsonl")}
    main = [r for r in load_responses(settings.responses) if r.condition == config.main_condition]
    picked = sample(main, settings.human_sample_share, settings.human_sample_seed)

    def translate(text: str) -> str:
        request = ChatRequest(
            model=config.judge.model,
            messages=(("user", TRANSLATE_PROMPT.format(text=text)),),
            temperature=config.judge.temperature,
            max_tokens=config.answer.max_tokens,
        )
        return client.chat(request).content

    def item(response: Response) -> SampleItem:
        case = cases[response.item_id]
        fields = {"question": case.question, "gold": gold_target(case), "response": response.response}
        translation = {k: translate(v) for k, v in fields.items()} if case.lang in settings.translate_for_review else None
        return SampleItem(key=response_key(response), lang=case.lang, translation=translation, **fields)

    with ThreadPoolExecutor(max_workers=settings.concurrency) as pool:
        items = list(pool.map(item, picked))
    page = settings.human_page_template.read_text(encoding="utf-8").replace(
        "__ITEMS__", json.dumps([i.model_dump() for i in items], ensure_ascii=False)
    )
    settings.human_page.parent.mkdir(parents=True, exist_ok=True)
    settings.human_page.write_text(page, encoding="utf-8")
    return settings.human_page


def cohen_kappa(pairs: list[tuple[str, str]]) -> float:
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    first, second = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(first[label] * second[label] for label in first) / n**2
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0


def agreement(settings: Settings, responses: list[Response]) -> dict | None:
    """Judge-human agreement on the graded sample; None until the human grades are in the repository."""
    if not settings.human_grades.exists():
        return None
    with settings.human_grades.open(encoding="utf-8") as f:
        human = {g.key: g.grade for g in (HumanGrade.model_validate_json(line) for line in f if line.strip())}
    pairs = [(r.grade or "ungraded", human[response_key(r)]) for r in responses if response_key(r) in human]
    return {
        "n": len(pairs),
        "agreement": sum(a == b for a, b in pairs) / len(pairs),
        "cohen_kappa": cohen_kappa(pairs),
        "confusion": {f"judge={a} human={b}": count for (a, b), count in sorted(Counter(pairs).items())},
    }
