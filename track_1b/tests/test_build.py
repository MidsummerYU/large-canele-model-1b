from newcomer_qa.build import longest_copied_run

EVIDENCE = "In der Regel müssen Sie sich innerhalb von 14 Tagen nach Ihrem Umzug bei der neuen Wohngemeinde anmelden."


def test_longest_copied_run_counts_consecutive_words_shared_with_the_source():
    assert longest_copied_run("Wie lange habe ich Zeit, mich anzumelden?", EVIDENCE) == 0
    assert longest_copied_run("Muss ich mich innerhalb von 14 Tagen anmelden?", EVIDENCE) == 4
    assert longest_copied_run("Muss ich mich nach Ihrem Umzug bei der neuen Wohngemeinde anmelden?", EVIDENCE) == 8


def test_longest_copied_run_matches_whole_words_only():
    assert longest_copied_run("Tag", EVIDENCE) == 0
