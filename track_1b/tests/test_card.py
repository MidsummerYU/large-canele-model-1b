from newcomer_qa.card import card_context, write_card
from newcomer_qa.config import Settings
from newcomer_qa.technical_report import write_report


def test_the_card_counts_match_the_dataset_files(tmp_path):
    settings = Settings(card=tmp_path / "card.md")
    context = card_context(settings)
    assert context["candidates"] == sum(context["consensus"].values())
    assert context["regular_items"] == context["candidates"] - context["consensus"]["drop"] - context["adjudication"]["drop"]
    assert context["items"] == context["regular_items"] + context["edge_items"]
    for kind in context["edge"].values():
        assert kind["kept"] == kind["sources"] - kind["skipped"] - kind["dropped"]
    text = write_card(settings).read_text()
    assert text.startswith("---\nlicense: cdla-permissive-2.0") and "[More Information Needed]" not in text


def test_the_report_fills_every_placeholder(tmp_path):
    text = write_report(Settings(report_path=tmp_path / "report.md")).read_text()
    assert text.startswith("# Technical report") and "{" not in text
