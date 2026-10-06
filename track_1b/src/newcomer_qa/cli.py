import argparse

from newcomer_qa.config import Settings
from newcomer_qa.fetch import fetch
from newcomer_qa.generate import generate
from newcomer_qa.review import review_sheet


def main() -> None:
    parser = argparse.ArgumentParser(prog="newcomer-qa")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("fetch", help="fetch the ch.ch pages in data/sources.yaml into data/raw/")
    commands.add_parser("generate", help="draft candidate questions from the fetched pages with Apertus")
    commands.add_parser("review-sheet", help="write the candidates to a CSV for human review")
    args = parser.parse_args()

    settings = Settings()
    if args.command == "fetch":
        fetch(settings)
    elif args.command == "generate":
        generate(settings)
    elif args.command == "review-sheet":
        review_sheet(settings)
