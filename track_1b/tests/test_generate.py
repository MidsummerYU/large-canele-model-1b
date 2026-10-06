from datetime import UTC, datetime

from newcomer_qa.chch import Page, Passage
from newcomer_qa.fetch import StoredPage
from newcomer_qa.generate import parse_candidates

PAGE = StoredPage(
    page_id="moving-house",
    topic="registration",
    seed_path="/de/wohnen/umzug/",
    fetched_at=datetime(2026, 10, 6, tzinfo=UTC),
    page=Page(
        url="https://www.example.ch/en/moving-house/",
        lang="en",
        title="Moving house",
        modified_at=None,
        passages=[Passage(heading="Moving", text="Register within 14 days."),
                  Passage(heading="Moving", text="Bring your passport.")],
        alternates={},
    ),
)

REPLY = """QUESTION: How long do I have to register with my new commune after moving?
ANSWER: 14 days
VARIANTS: two weeks | within 14 days
EVIDENCE: 1

QUESTION: Which document do I bring to register?
ANSWER: A passport
VARIANTS:
EVIDENCE: [2]

QUESTION: Can I register online?
ANSWAR: Yes
EVIDENCE: 1

QUESTION: Do I need my rental contract?
ANSWER: Yes
EVIDENCE: 2

QUESTION: Is registration free?
ANSWER: Yes
VARIANTS: it costs nothing
EVIDENCE: 7
"""


def test_one_malformed_block_does_not_swallow_the_next_one():
    candidates, rejected = parse_candidates(REPLY, PAGE, "org/model-70B")

    assert rejected == {"malformed block": 1, "evidence passage does not exist": 1}
    assert [(c.candidate_id, c.question, c.answer, c.variants, c.evidence) for c in candidates] == [
        ("en-moving-house-01", "How long do I have to register with my new commune after moving?",
         "14 days", ["two weeks", "within 14 days"], 0),
        ("en-moving-house-02", "Which document do I bring to register?", "A passport", [], 1),
        ("en-moving-house-03", "Do I need my rental contract?", "Yes", [], 1),
    ]
    assert candidates[0].url == PAGE.page.url
    assert candidates[2].evidence_text == "Bring your passport."
