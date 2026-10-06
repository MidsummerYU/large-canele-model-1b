import argparse

from newcomer_qa.build import build_dataset
from newcomer_qa.card import package_hf, write_card
from newcomer_qa.config import Settings
from newcomer_qa.consensus import consensus
from newcomer_qa.evaluate import EvalConfig, evaluate
from newcomer_qa.fetch import fetch
from newcomer_qa.generate import generate
from newcomer_qa.figures import write_figures
from newcomer_qa.human import agreement, write_human_page
from newcomer_qa.pdf import build_pdf, page_count
from newcomer_qa.review import review_sheet
from newcomer_qa.score import write_scores
from newcomer_qa.technical_report import write_report


def main() -> None:
    parser = argparse.ArgumentParser(prog="newcomer-qa")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("fetch", help="fetch the ch.ch pages in data/sources.yaml into data/raw/")
    commands.add_parser("generate", help="draft candidate questions from the fetched pages with Apertus")
    commands.add_parser("review-sheet", help="write the candidates to a CSV for human review")
    commands.add_parser("consensus", help="combine independent reviews: agreement, outcomes, adjudication packet")
    commands.add_parser("build-dataset", help="write the reviewed test cases and metadata to data/dataset/")
    evaluate_parser = commands.add_parser("evaluate", help="answer every test case with each model and grade it")
    evaluate_parser.add_argument("--mode", choices=["live", "replay"], default="replay", help="replay never calls the API")
    evaluate_parser.add_argument("--update", action="store_true", help="overwrite results/scores.json instead of checking it")
    human_parser = commands.add_parser("human-page", help="write the blind judge-check page for a random 20% sample")
    human_parser.add_argument("--mode", choices=["live", "replay"], default="replay", help="live translates new items")
    commands.add_parser("report-pdf", help="print technical_report.md to the submission PDF with headless Chrome")
    commands.add_parser("package-hf", help="write hf/: the dataset card as README.md and the data files to upload")
    args = parser.parse_args()

    settings = Settings()
    if args.command == "fetch":
        fetch(settings)
    elif args.command == "generate":
        generate(settings)
    elif args.command == "review-sheet":
        review_sheet(settings)
    elif args.command == "consensus":
        consensus(settings)
    elif args.command == "build-dataset":
        build_dataset(settings)
    elif args.command == "evaluate":
        responses = evaluate(settings, args.mode)
        config = EvalConfig.load(settings.eval_config)
        path = write_scores(responses, settings.results_dir, args.update, config.primary_grader, agreement(settings, responses))
        print((path.parent / "summary.md").read_text(encoding="utf-8"))
        figures = write_figures(path, list(config.models), list(config.conditions), config.main_condition, settings.figures_dir)
        for written in [write_card(settings), *figures, write_report(settings)]:
            print(f"wrote {written.relative_to(settings.report_path.parent)}")
    elif args.command == "report-pdf":
        pdf = build_pdf(settings)
        print(f"wrote {pdf.name} ({page_count(pdf)} pages)")
    elif args.command == "package-hf":
        print(f"wrote {package_hf(settings)}")
    elif args.command == "human-page":
        print(f"wrote {write_human_page(settings, args.mode)}")
