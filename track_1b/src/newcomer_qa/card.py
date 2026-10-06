import json
from collections import Counter
from pathlib import Path
from statistics import mean

from newcomer_qa.build import Metadata, ReviewLogEntry, TestCase
from newcomer_qa.config import Settings
from newcomer_qa.consensus import fleiss_kappa
from newcomer_qa.evaluate import EvalConfig, load_test_cases


def _jsonl(path: Path, model):
    with path.open(encoding="utf-8") as f:
        return [model.model_validate_json(line) for line in f if line.strip()]


def _table(header: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join([*lines, *("| " + " | ".join(str(c) for c in row) + " |" for row in rows)])


def _composition(cases: list[TestCase]) -> str:
    languages = sorted({c.lang for c in cases})
    counts = Counter((c.topic, c.lang) for c in cases)
    rows = [[topic, *(counts[topic, lang] for lang in languages), sum(counts[topic, lang] for lang in languages)]
            for topic in sorted({c.topic for c in cases})]
    rows.append(["**all**", *(sum(c.lang == lang for c in cases) for lang in languages), f"**{len(cases)}**"])
    return _table(["topic", *languages, "all"], rows)


def _results(scores: dict, key: str) -> str:
    rows = []
    for name, by_field in scores[key].items():
        s = by_field["all"]["all"]
        rows.append([name, f"{s['correct']:.1%}", f"{s['incorrect']:.1%}", f"{s['not_attempted']:.1%}",
                     f"{s['accuracy_given_attempted']:.1%}", f"{s['f1']:.3f}"])
    return _table(["model/condition", "correct", "incorrect", "not attempted", "correct given attempted", "F1"], rows)


def _agreement(scores: dict) -> str:
    rows = [[name, a["n"], f"{a['agreement']:.1%}", f"{a['cohen_kappa']:.3f}"] for name, a in scores["grader_agreement"].items()]
    return _table(["comparison", "n", "agreement", "Cohen's kappa"], rows)


def card_context(settings: Settings) -> dict:
    cases = load_test_cases(settings.dataset_dir / "test_cases.jsonl")
    metadata = _jsonl(settings.dataset_dir / "metadata.jsonl", Metadata)
    log = _jsonl(settings.dataset_dir / "review_log.jsonl", ReviewLogEntry)
    scores = json.loads((settings.results_dir / "scores.json").read_text(encoding="utf-8"))
    config = EvalConfig.load(settings.eval_config)
    reviewers = sorted(log[0].review_votes)
    consensus = Counter(e.consensus for e in log)
    adjudication = Counter(e.adjudication for e in log if e.adjudication)
    fetched = sorted(m.source_fetched_at.date().isoformat() for m in metadata)
    modified = sorted(m.source_modified_at.date().isoformat() for m in metadata if m.source_modified_at)
    return {
        "items": len(cases),
        "languages": ", ".join(sorted({c.lang for c in cases})),
        "topics": len({c.topic for c in cases}),
        "composition": _composition(cases),
        "answers_mean": mean(len(c.answers) for c in cases),
        "pages": len({m.source_url for m in metadata}),
        "fetched_from": fetched[0],
        "fetched_to": fetched[-1],
        "modified_from": modified[0],
        "modified_to": modified[-1],
        "candidates": len(log),
        "reviewers": ", ".join(settings.reviewer_models[r] for r in reviewers),
        "consensus": consensus,
        "adjudication": adjudication,
        "kappa": fleiss_kappa([[e.review_votes[r] for r in reviewers] for e in log]),
        "reworded": sum(m.question_reworded for m in metadata),
        "tags": Counter(t for m in metadata for t in m.tags),
        "drafted_by": ", ".join(sorted({m.drafted_by for m in metadata})),
        "max_copied_words": settings.max_copied_words,
        "generator_temperature": settings.generator_temperature,
        "max_questions_per_page": settings.max_questions_per_page,
        "license": settings.dataset_license,
        "config": config,
        "primary": scores["primary_grader"],
        "results": _results(scores, "scores"),
        "judge_results": _results(scores, "judge_scores"),
        "agreement": _agreement(scores),
        "s": scores["scores"],
        "j": scores["judge_scores"],
    }


def write_card(settings: Settings) -> Path:
    text = settings.card_template.read_text(encoding="utf-8").format(**card_context(settings))
    settings.card.write_text(text, encoding="utf-8")
    return settings.card


HF_FILES = ("test_cases.jsonl", "responses.jsonl", "metadata.jsonl", "review_log.jsonl")


def package_hf(settings: Settings) -> Path:
    """The folder to upload as the Hugging Face dataset: the card as README.md and the data files under data/."""
    data = settings.hf_dir / "data"
    data.mkdir(parents=True, exist_ok=True)
    (settings.hf_dir / "README.md").write_text(settings.card.read_text(encoding="utf-8"), encoding="utf-8")
    for name in HF_FILES:
        (data / name).write_bytes((settings.dataset_dir / name).read_bytes())
    return settings.hf_dir
