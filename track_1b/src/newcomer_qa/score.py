import json
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel

from newcomer_qa.edge import FACT_KIND
from newcomer_qa.evaluate import Grade, Response


class Scores(BaseModel):
    n: int
    correct: float
    incorrect: float
    not_attempted: float
    ungraded: float
    accuracy_given_attempted: float
    f1: float


class ScoresMismatchError(AssertionError):
    pass


def scores(grades: list[Grade | None]) -> Scores:
    n = len(grades)
    share = {grade: sum(g == grade for g in grades) / n for grade in ("correct", "incorrect", "not_attempted")}
    attempted = share["correct"] + share["incorrect"]
    given_attempted = share["correct"] / attempted if attempted else 0.0
    # SimpleQA's F-score: harmonic mean of overall correct and correct given attempted.
    f1 = 2 * given_attempted * share["correct"] / (given_attempted + share["correct"]) if share["correct"] else 0.0
    return Scores(
        n=n,
        **share,
        ungraded=sum(g is None for g in grades) / n,
        accuracy_given_attempted=given_attempted,
        f1=f1,
    )


def breakdown(responses: list[Response], grader: str = "grade") -> dict[str, dict[str, dict[str, Scores]]]:
    """"<model>/<condition>" -> "all" / "lang" / "topic" -> group -> scores, using the `grader` field of each response."""
    by_model: dict[str, list[Response]] = defaultdict(list)
    for response in responses:
        by_model[f"{response.model}/{response.condition}"].append(response)
    table = {}
    for model, rows in by_model.items():
        table[model] = {"all": {"all": scores([getattr(r, grader) for r in rows])}}
        for field in ("lang", "topic", "kind"):
            groups: dict[str, list[Response]] = defaultdict(list)
            for row in rows:
                groups[getattr(row, field)].append(row)
            table[model][field] = {name: scores([getattr(r, grader) for r in group]) for name, group in sorted(groups.items())}
    return table


def _overall(table: dict[str, dict[str, dict[str, Scores]]]) -> list[str]:
    lines = ["| model/condition | correct | incorrect | not attempted | correct given attempted | F1 |", "|---|---|---|---|---|---|"]
    for model, by_field in table.items():
        s = by_field["all"]["all"]
        lines.append(f"| {model} | {s.correct:.1%} | {s.incorrect:.1%} | {s.not_attempted:.1%} | {s.accuracy_given_attempted:.1%} | {s.f1:.3f} |")
    return lines


def summary_markdown(
    table: dict[str, dict[str, dict[str, Scores]]],
    judge_table: dict[str, dict[str, dict[str, Scores]]],
    kind_table: dict[str, dict[str, dict[str, Scores]]],
    primary: str,
    agreement: dict[str, dict],
) -> str:
    lines = ["# Closed-book results", "", f"SimpleQA grades by `{primary}` (see data/eval.yaml).", ""]
    lines += ["## Grader agreement", "", "| comparison | n | agreement | Cohen's kappa |", "|---|---|---|---|"]
    lines += [f"| {name} | {a['n']} | {a['agreement']:.1%} | {a['cohen_kappa']:.3f} |" for name, a in agreement.items()]
    lines += ["", "## Overall as graded by the in-harness Apertus judge, for comparison", "", *_overall(judge_table), ""]
    lines += ["## By item kind (regular facts and edge cases)", "", "| model/condition | kind | n | correct | incorrect | not attempted |", "|---|---|---|---|---|---|"]
    for model, by_field in kind_table.items():
        for kind, k in by_field["kind"].items():
            lines.append(f"| {model} | {kind} | {k.n} | {k.correct:.1%} | {k.incorrect:.1%} | {k.not_attempted:.1%} |")
    lines.append("")
    lines += ["# Regular fact items", ""]
    for field in ("all", "lang", "topic"):
        lines += [
            f"## By {field}" if field != "all" else "## Overall",
            "",
            "| model/condition | group | n | correct | incorrect | not attempted | correct given attempted | F1 |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for model, by_field in table.items():
            for group, s in by_field[field].items():
                lines.append(
                    f"| {model} | {group} | {s.n} | {s.correct:.1%} | {s.incorrect:.1%} | {s.not_attempted:.1%} "
                    f"| {s.accuracy_given_attempted:.1%} | {s.f1:.3f} |"
                )
        lines.append("")
    return "\n".join(lines)


def _dump(table: dict[str, dict[str, dict[str, Scores]]]) -> dict:
    return {m: {f: {g: s.model_dump() for g, s in v.items()} for f, v in d.items()} for m, d in table.items()}


def write_scores(responses: list[Response], results_dir: Path, update: bool, primary: str, agreement: dict[str, dict]) -> Path:
    """Write the scores; unless `update`, first check them against the committed ones.

    The headline tables cover the regular fact items only; the edge cases are scored by kind on their own.
    """
    facts = [r for r in responses if r.kind == FACT_KIND]
    table, judge_table, kind_table = breakdown(facts), breakdown(facts, "judge_grade"), breakdown(responses)
    content = {
        "primary_grader": primary,
        "scores": _dump(table),
        "judge_scores": _dump(judge_table),
        "kind_scores": _dump(kind_table),
        "grader_agreement": agreement,
    }
    document = json.dumps(content, indent=2) + "\n"
    path = results_dir / "scores.json"
    if path.exists() and not update and path.read_text(encoding="utf-8") != document:
        raise ScoresMismatchError(f"recomputed scores differ from {path}; rerun with --update if the change is intended")
    results_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")
    (results_dir / "summary.md").write_text(summary_markdown(table, judge_table, kind_table, primary, agreement), encoding="utf-8")
    return path
