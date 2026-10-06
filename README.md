# Swiss Newcomer QA — do language models know the rules newcomers to Switzerland must follow?

Evaluation dataset and harness for **Hack Apertus, Track 1B** (Swiss Voices, core task intelligence). Closed-book
questions in German, French, Italian and English about registering with the commune, residence permits, health
insurance, the AHV/AVS pension system, withholding tax and naturalisation, each with accepted answers and a source
page on [ch.ch](https://www.ch.ch). Apertus 1.5 8B and 70B are graded with SimpleQA (correct / incorrect / not
attempted).

- Dataset card: [`track_1b/docs/dataset_card.md`](track_1b/docs/dataset_card.md) (also the Hugging Face README)
- Report: [`track_1b/technical_report.md`](track_1b/technical_report.md), PDF [`track_1b/LargeCaneleModel_Report.pdf`](track_1b/LargeCaneleModel_Report.pdf)
- Results: [`track_1b/results/summary.md`](track_1b/results/summary.md)
- Challenge rules: [`track_1b/README.md`](track_1b/README.md)

## Reproduce

Requirements: Docker and `make`. No API key, no GPU, no model weights.

```bash
cd track_1b
make run     # replay every answer and judge call, recompute the scores, fail if they differ from results/scores.json
make test    # run the test suite in the same image
git status   # empty: the scores, dataset card, figures and report were rebuilt byte for byte
```

`make run` mounts the checkout into the container and writes back `results/`, `docs/dataset_card.md`,
`docs/figures/` and `technical_report.md`. Without Docker: `uv run newcomer-qa evaluate` and `uv run pytest`.

## How it works

```
ch.ch pages ─► draft (Apertus 70B) ─► 3 blind AI reviews ─► consensus / adjudication ─► checks ─► test cases
                                                                                                  │
         answers (8B, 70B × 2 conditions) ◄─ recording client (replay or live) ◄─────────────────────┘
                     │
                     ├─► Apertus judge (in harness, recorded) ─┐
                     └─► committed grades (Claude Opus, all;   ├─► SimpleQA scores, agreement ─► card, figures, report
                         Claude Sonnet, 20% sample) ───────────┘
```

1. **Build** (needs the page text, which is not redistributed): `make fetch` stores ch.ch pages locally,
   `make generate` drafts candidates with Apertus 70B, `make review-sheet` and `make consensus` combine three blind
   AI reviews, and `make build-dataset` writes `data/dataset/` (test cases, metadata, review log) after the language
   and copy checks. The rules are in `docs/annotation-guidelines.md`.
2. **Evaluate** (`newcomer-qa evaluate`): every test case is asked to every model in `data/eval.yaml`, once per
   condition (`swiss_context` adds "I live in Switzerland." in the question's language, `as_asked` does not). The
   Apertus judge grades each answer with the unchanged SimpleQA prompt (`data/grader/`). Every call is recorded in
   `data/recordings/` and keyed by a hash of the request, so replays are exact.
3. **Grade and score**: the headline grades come from `data/grades/<primary_grader>.jsonl` (Claude Opus 5.5, applied
   offline to blinded items). `score.py` computes SimpleQA's rates, accuracy given attempted and F1 by model,
   condition, language and topic, and the agreement (with Cohen's kappa) between the judge and every committed
   grader. Unless `--update` is given, the run fails when the scores differ from the committed ones.
4. **Document**: `card.py`, `figures.py` and `technical_report.py` fill the card and report templates in `docs/`
   from the same files, so no number is typed by hand.

## Layout

| Path (under `track_1b/`) | Contents |
|---|---|
| `src/newcomer_qa/` | `fetch`, `chch` (page parsing), `generate`, `review`, `consensus`, `build`, `client`, `evaluate`, `score`, `human` (sampling, agreement, judge-check page), `card`, `figures`, `technical_report`, `pdf` |
| `data/sources.yaml` | the ch.ch seed pages per topic |
| `data/dataset/` | `test_cases.jsonl`, `metadata.jsonl`, `review_log.jsonl`, `responses.jsonl` (the Hugging Face files) |
| `data/eval.yaml` | endpoint, models, conditions, sampling, judge and primary grader: every evaluation setting |
| `data/grader/` | the SimpleQA grader prompt (MIT, OpenAI simple-evals) |
| `data/grades/` | committed grades, one file per grader |
| `data/recordings/` | every evaluation call; generation calls contain page text and stay in the unpublished `data/raw/` |
| `data/human/judge_check.html` | blind judge-check page for a human grader (1/2/3 keys, exports a grades file) |
| `docs/` | annotation guidelines, consent form template, card and report templates, generated card and figures |
| `results/` | `scores.json` (expected results, checked by `make run`) and `summary.md` |

## Extend it

- **Evaluate a new model:** add it under `models` in `data/eval.yaml`, put `LLM_API_KEY` in `.env` and run
  `make evaluate`. Its answers are recorded and judged by Apertus; for headline numbers grade them with the same
  SimpleQA rules and add the grades to `data/grades/`.
- **Add a condition:** add a name and a sentence per language under `conditions` in `data/eval.yaml`.
- **Add a human check:** open `data/human/judge_check.html`, grade, export, and save the file as
  `data/grades/human.jsonl`; the agreement table picks it up.
- **Add topics or pages:** extend `data/sources.yaml` and rerun the build steps.

## Configuration

Settings are read from the environment or `track_1b/.env`: `LLM_BASE_URL` and `LLM_API_KEY` for live calls, and
`CHROME` for `make report`. Every setting and its default is declared once in `track_1b/src/newcomer_qa/config.py`;
evaluation settings are in `data/eval.yaml`.

## License

Code: Apache-2.0 ([LICENSE](LICENSE)). Report and documentation: CC-BY-4.0. Dataset: CDLA-Permissive-2.0. ch.ch
content is © Swiss Federal Chancellery and is not redistributed; the dataset contains facts, our own wording and
links.
