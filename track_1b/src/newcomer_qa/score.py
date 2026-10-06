import json
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel

from newcomer_qa.evaluate import Response


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


def scores(responses: list[Response]) -> Scores:
    n = len(responses)
    share = {grade: sum(r.grade == grade for r in responses) / n for grade in ("correct", "incorrect", "not_attempted")}
    attempted = share["correct"] + share["incorrect"]
    given_attempted = share["correct"] / attempted if attempted else 0.0
    # SimpleQA's F-score: harmonic mean of overall correct and correct given attempted.
    f1 = 2 * given_attempted * share["correct"] / (given_attempted + share["correct"]) if share["correct"] else 0.0
    return Scores(
        n=n,
        **share,
        ungraded=sum(r.grade is None for r in responses) / n,
        accuracy_given_attempted=given_attempted,
        f1=f1,
    )


def breakdown(responses: list[Response]) -> dict[str, dict[str, dict[str, Scores]]]:
    """"<model>/<condition>" -> "all" / "lang" / "topic" -> group -> scores."""
    by_model: dict[str, list[Response]] = defaultdict(list)
    for response in responses:
        by_model[f"{response.model}/{response.condition}"].append(response)
    table = {}
    for model, rows in by_model.items():
        table[model] = {"all": {"all": scores(rows)}}
        for field in ("lang", "topic"):
            groups: dict[str, list[Response]] = defaultdict(list)
            for row in rows:
                groups[getattr(row, field)].append(row)
            table[model][field] = {name: scores(group) for name, group in sorted(groups.items())}
    return table


def summary_markdown(table: dict[str, dict[str, dict[str, Scores]]], agreement: dict[str, dict]) -> str:
    lines = ["# Closed-book results", "", "SimpleQA grading by the judge in data/eval.yaml.", ""]
    lines += ["## Grader agreement on the sample", "", "| comparison | n | agreement | Cohen's kappa |", "|---|---|---|---|"]
    lines += [f"| {name} | {a['n']} | {a['agreement']:.1%} | {a['cohen_kappa']:.3f} |" for name, a in agreement.items()]
    lines.append("")
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


def write_scores(responses: list[Response], results_dir: Path, update: bool, agreement: dict[str, dict] | None = None) -> Path:
    """Write the scores; unless `update`, first check them against the committed ones."""
    table = breakdown(responses)
    content = {m: {f: {g: s.model_dump() for g, s in v.items()} for f, v in d.items()} for m, d in table.items()}
    agreement = agreement or {}
    document = json.dumps({"scores": content, "grader_agreement": agreement}, indent=2) + "\n"
    path = results_dir / "scores.json"
    if path.exists() and not update and path.read_text(encoding="utf-8") != document:
        raise ScoresMismatchError(f"recomputed scores differ from {path}; rerun with --update if the change is intended")
    results_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")
    (results_dir / "summary.md").write_text(summary_markdown(table, agreement), encoding="utf-8")
    return path
