import re
from collections import defaultdict
from pathlib import Path

from newcomer_qa.card import card_context
from newcomer_qa.config import Settings
from newcomer_qa.edge import FACT_KIND
from newcomer_qa.human import cohen_kappa, load_responses


# Phrases a reply uses to say a rule differs between cantons or communes, in the four dataset languages.
CANTONAL_HEDGE = re.compile(
    r"je nach (Kanton|Gemeinde)|von Kanton zu Kanton|kantonal (unterschiedlich|verschieden)"
    r"|selon (le|les) (canton|commune)|d'un canton à l'autre|varie(nt)? selon"
    r"|a seconda del (cantone|comune)|da cantone a cantone"
    r"|depend(s|ing)? on (the|your) (canton|commune|municipality)|var(y|ies) (by|from|between) canton",
    re.IGNORECASE,
)


def _cantonal_hedge_on_facts(settings: Settings, condition: str) -> dict[str, float]:
    """Model -> share of its replies to regular facts that say the rule differs by canton."""
    replies: dict[str, list[bool]] = defaultdict(list)
    for r in load_responses(settings.responses):
        if r.condition == condition and r.kind == FACT_KIND:
            replies[r.model].append(bool(CANTONAL_HEDGE.search(r.response)))
    return {model: sum(flags) / len(flags) for model, flags in replies.items()}


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
    context["hedge"] = _cantonal_hedge_on_facts(settings, context["config"].main_condition)
    text = settings.report_template.read_text(encoding="utf-8").format(**context)
    settings.report_path.write_text(text, encoding="utf-8")
    return settings.report_path
