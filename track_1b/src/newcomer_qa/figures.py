import json
from pathlib import Path

import matplotlib
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator

SURFACE, INK, INK_SECONDARY, MUTED, GRID, BASELINE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SERIES = ("#2a78d6", "#eb6834")
GRADE_COLOURS = {"correct": "#2a78d6", "incorrect": "#eb6834", "not_attempted": "#c3c2b7"}

STYLE = {
    # Bundled with matplotlib, so the SVGs come out identical on every machine.
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "svg.hashsalt": "newcomer-qa",
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK_SECONDARY,
    "axes.titlesize": 9,
    "axes.titlecolor": INK,
    "axes.titlelocation": "left",
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelcolor": INK_SECONDARY,
    "ytick.labelcolor": INK_SECONDARY,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.5,
    "legend.frameon": False,
}


def _percent_axis(ax, limit: float = 1.0, step: float = 0.2) -> None:
    ax.set_xlim(0, limit)
    ax.xaxis.set_major_locator(MultipleLocator(step))
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.grid(axis="y", visible=False)


def outcomes(scores: dict, path: Path) -> None:
    rows = list(scores["scores"])
    fig = Figure(figsize=(6.6, 1.9), layout="constrained")
    ax = fig.subplots()
    for y, row in enumerate(rows):
        left = 0.0
        s = scores["scores"][row]["all"]["all"]
        for grade, colour in GRADE_COLOURS.items():
            ax.barh(y, s[grade], left=left, height=0.62, color=colour, edgecolor=SURFACE, linewidth=1.5,
                    label=grade.replace("_", " ") if y == 0 else None)
            if s[grade] >= 0.06:
                ax.text(left + s[grade] / 2, y, f"{s[grade]:.0%}", ha="center", va="center", fontsize=7,
                        color=SURFACE if grade != "not_attempted" else INK)
            left += s[grade]
    ax.set_yticks(range(len(rows)), [r.replace("/", " · ").replace("_", " ") for r in rows])
    ax.invert_yaxis()
    _percent_axis(ax)
    fig.legend(*ax.get_legend_handles_labels(), loc="outside lower center", ncols=len(GRADE_COLOURS))
    fig.savefig(path, metadata={"Date": None})


def _dumbbell(ax, rows: list[tuple[str, list[float]]], labels: list[str]) -> None:
    for y, (_, values) in enumerate(rows):
        ax.plot([min(values), max(values)], [y, y], color=BASELINE, linewidth=1.5, zorder=1)
        for value, colour, label in zip(values, SERIES, labels):
            ax.scatter(value, y, s=36, color=colour, edgecolors=SURFACE, linewidths=1.5, zorder=2, label=label if y == 0 else None)
    ax.set_yticks(range(len(rows)), [label for label, _ in rows])


def _panels(models: list[str], height: float = 2.0) -> tuple[Figure, list]:
    fig = Figure(figsize=(6.6, height), layout="constrained")
    axes = list(fig.subplots(1, len(models), sharey=True))
    axes[0].invert_yaxis()
    return fig, axes


def judge_leniency(scores: dict, models: list[str], condition: str, path: Path) -> None:
    fig, axes = _panels(models)
    for ax, model in zip(axes, models):
        key = f"{model}/{condition}"
        rows = [(lang, [scores[t][key]["lang"][lang]["incorrect"] for t in ("scores", "judge_scores")]) for lang in scores["scores"][key]["lang"]]
        _dumbbell(ax, rows, [scores["primary_grader"], "Apertus judge"])
        ax.set_title(f"Incorrect answers, {model} · {condition.replace('_', ' ')}")
        _percent_axis(ax, 0.6, 0.1)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncols=2)
    fig.savefig(path, metadata={"Date": None})


def context_effect(scores: dict, models: list[str], conditions: list[str], path: Path) -> None:
    fig, axes = _panels(models)
    for ax, model in zip(axes, models):
        languages = scores["scores"][f"{model}/{conditions[0]}"]["lang"]
        rows = [(lang, [scores["scores"][f"{model}/{c}"]["lang"][lang]["correct"] for c in conditions]) for lang in languages]
        _dumbbell(ax, rows, [c.replace("_", " ") for c in conditions])
        ax.set_title(f"Correct answers, {model}")
        _percent_axis(ax, 0.8, 0.2)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncols=len(conditions))
    fig.savefig(path, metadata={"Date": None})


def write_figures(scores_path: Path, models: list[str], conditions: list[str], main_condition: str, figures_dir: Path) -> list[Path]:
    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    figures_dir.mkdir(parents=True, exist_ok=True)
    paths = [figures_dir / name for name in ("outcomes.svg", "judge_leniency.svg", "context_effect.svg")]
    with matplotlib.rc_context(STYLE):
        outcomes(scores, paths[0])
        judge_leniency(scores, models, main_condition, paths[1])
        context_effect(scores, models, conditions, paths[2])
    return paths
