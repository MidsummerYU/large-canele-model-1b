import pytest

from newcomer_qa import build
from newcomer_qa.evaluate import Response, gold_target, parse_grade
from newcomer_qa.human import cohen_kappa, response_key, sample
from newcomer_qa.score import ScoresMismatchError, scores, write_scores


@pytest.mark.parametrize(("output", "grade"), [("A", "correct"), ("B", "incorrect"), (" C\n", "not_attempted"), ("none", None)])
def test_the_judge_letter_maps_to_a_grade(output, grade):
    assert parse_grade(output) == grade


def test_every_accepted_answer_is_shown_to_the_judge():
    case = build.TestCase(item_id="x", lang="en", topic="t", question="?", answers=["one day", "1 day"])
    assert gold_target(case) == "one day (also acceptable: 1 day)"


def _responses(*grades):
    return [
        Response(item_id=str(i), lang="en", topic="t", model="m", condition="c", response="", grade=g, judge_output="")
        for i, g in enumerate(grades)
    ]


def test_scores_follow_simpleqa_definitions():
    s = scores(_responses("correct", "correct", "incorrect", "not_attempted"))
    assert (s.correct, s.not_attempted) == (0.5, 0.25)
    assert s.accuracy_given_attempted == pytest.approx(2 / 3)
    assert s.f1 == pytest.approx(2 * 0.5 * (2 / 3) / (0.5 + 2 / 3))


def test_changed_scores_are_refused_unless_updated(tmp_path):
    write_scores(_responses("correct"), tmp_path, update=False)
    with pytest.raises(ScoresMismatchError):
        write_scores(_responses("incorrect"), tmp_path, update=False)
    write_scores(_responses("incorrect"), tmp_path, update=True)


def test_the_human_sample_is_a_seeded_share_of_each_model():
    rows = [r.model_copy(update={"model": m}) for m in ("8B", "70B") for r in _responses(*["correct"] * 10)]
    first, second = sample(rows, 0.2, seed=1), sample(rows, 0.2, seed=1)
    assert [response_key(r) for r in first] == [response_key(r) for r in second]
    assert sorted(r.model for r in first) == ["70B", "70B", "8B", "8B"]


def test_kappa_is_one_for_perfect_agreement_and_zero_for_chance():
    assert cohen_kappa([("correct", "correct"), ("incorrect", "incorrect")]) == 1.0
    assert cohen_kappa([("correct", "correct"), ("correct", "incorrect"), ("incorrect", "correct"), ("incorrect", "incorrect")]) == 0.0
