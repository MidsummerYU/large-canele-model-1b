.PHONY: run image fetch generate review-sheet consensus build-dataset evaluate human-page test

IMAGE := newcomer-qa
# The checkout is mounted at /app, so the results are written back to it as the host user, not root.
DOCKER_RUN := docker run --rm --user $$(id -u):$$(id -g) -v "$(CURDIR):/app"

image:
	docker build -t $(IMAGE) .

# Replays every recorded answer and grade, recomputes the scores and fails if they differ from
# results/scores.json; needs no API key.
run: image
	$(DOCKER_RUN) $(IMAGE) evaluate

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

evaluate:
	uv run newcomer-qa evaluate --mode live

human-page:
	uv run newcomer-qa human-page --mode live

test: image
	$(DOCKER_RUN) --entrypoint /opt/venv/bin/pytest $(IMAGE) -q -p no:cacheprovider
