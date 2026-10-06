import pytest

from newcomer_qa.consensus import fleiss_kappa, outcome


def test_only_unanimous_keep_is_kept_and_majority_drop_is_dropped():
    assert outcome(["keep", "keep", "keep"]) == "keep"
    assert outcome(["drop", "drop", "keep"]) == "drop"
    assert outcome(["keep", "keep", "edit"]) == "adjudicate"
    assert outcome(["keep", "edit", "drop"]) == "adjudicate"


def test_fleiss_kappa_is_one_for_perfect_agreement_and_matches_a_hand_computed_case():
    assert fleiss_kappa([["keep"] * 3, ["drop"] * 3, ["edit"] * 3]) == pytest.approx(1.0)
    # Two items: one unanimous keep, one split keep/keep/drop.
    # P_i = 1 and 1/3, P_bar = 2/3; shares keep 5/6, drop 1/6, P_e = 26/36; kappa = (2/3 - 26/36) / (10/36) = -0.2
    assert fleiss_kappa([["keep"] * 3, ["keep", "keep", "drop"]]) == pytest.approx(-0.2)
