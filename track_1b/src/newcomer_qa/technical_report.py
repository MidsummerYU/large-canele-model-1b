from collections import defaultdict
from pathlib import Path

from newcomer_qa.card import card_context
from newcomer_qa.config import Settings
from newcomer_qa.human import cohen_kappa, load_responses


def _judge_agreement_by_language(settings: Settings, condition: str) -> dict[str, dict[str, float]]:
    """Agreement of the Apertus judge with the primary grades, per language, in one condition."""
    pairs: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for r in load_responses(settings.responses):
        if r.condition == condition and r.grade is not None:
            pairs[r.lang].append((r.judge_grade or "ungraded", r.grade))
    return {
        lang: {"agreement": sum(a == b for a, b in p) / len(p), "kappa": cohen_kappa(p)}
        for lang, p in sorted(pairs.items())
    }


def write_report(settings: Settings) -> Path:
    context = card_context(settings)
    context["by_lang"] = _judge_agreement_by_language(settings, context["config"].main_condition)
    text = settings.report_template.read_text(encoding="utf-8").format(**context)
    settings.report_path.write_text(text, encoding="utf-8")
    return settings.report_path
