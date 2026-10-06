.PHONY: run fetch generate review-sheet consensus build-dataset test

# Replace with the command that starts the project in a Docker container,
# e.g. `docker compose up`. It must work from a clean checkout.
run:
	@echo "make run is not implemented yet — edit this Makefile"; exit 1

fetch:
	uv run newcomer-qa fetch

generate:
	uv run newcomer-qa generate

review-sheet:
	uv run newcomer-qa review-sheet

consensus:
	uv run newcomer-qa consensus

build-dataset:
	uv run newcomer-qa build-dataset

test:
	uv run pytest -q
