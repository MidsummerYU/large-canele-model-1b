# Technical report — Swiss Newcomer QA: do Apertus models know the rules newcomers must follow?

> People who move to Switzerland must register, insure themselves and apply for permits within short deadlines, and increasingly ask chatbots how. We built {items} closed-book questions in German, French, Italian and English from the official portal ch.ch, each with accepted answers and a source, and graded Apertus 1.5 with SimpleQA. Even when told the user lives in Switzerland, Apertus 1.5 70B answers {s[70B/swiss_context][all][all][incorrect]:.0%} of the questions wrongly and declines only {s[70B/swiss_context][all][all][not_attempted]:.0%}; grading itself, it would report {j[70B/swiss_context][all][all][incorrect]:.0%}.

**Track:** Apertus Readiness - Track 1B (Swiss Voices, core task intelligence)  
**Event:** Online  
**Team:** Large Canelé Model — Yumeng Ye  
**Demo:** `make run` replays every model call and rebuilds the scores, figures, dataset card and this report; dataset: https://huggingface.co/datasets/{hf_repo}

----

### Use of Apertus

- **Model:** `{config.models[8B]}` and `{config.models[70B]}`
- **How it is used:** evaluation (closed-book answers), dataset drafting ({drafted_by} wrote the candidate questions) and an in-harness judge
- **Where it runs:** hosted endpoint, CSCS Inference Service (`{config.endpoint}`), chat completions, server-side chat template, no system prompt
- **Other models:** Claude Opus 5.5, Sonnet 5.5 and Fable 5.1 (Anthropic) reviewed and adjudicated the candidates and graded the answers (Opus: primary grades). Claude also assisted with the code and with drafting this text; the team reviewed it.

----

## Use Case Description

A newcomer to Switzerland must register with the commune soon after arriving, take out health insurance within three months, and understand residence permits, the AHV/AVS pension system and withholding tax, often before speaking a national language well. ch.ch, run by the Federal Chancellery with the cantons, explains these rules in German, French, Italian and English. An assistant built on a Swiss model should give the same correct rules in all four languages, and should say when it does not know instead of inventing a deadline or an amount. The dataset measures exactly that: correct, incorrect and not-attempted answers to the questions a newcomer asks, per language and topic.

## Dataset Summary

Each regular item is a single-turn question with one short factual answer (deadline, amount, age, number, office, document or yes/no) that holds everywhere in Switzerland, is stated explicitly on the cited ch.ch page, and is written in the page's language in our own words. The {items} items cover {topics} topics and come from {pages} pages (one seed page per subject plus its official French, Italian and English versions), so every language has its own questions about the same procedures:

{composition}

{edge_items} items are edge cases, where the right answer is not a fact but a qualification:

{edge_composition}

*cantonal* items ask as if there were one national rule where the page says it depends on the canton or commune; *false_premise* items take a wrong deadline, amount or obligation for granted, and the reference answer corrects it.

Items list {answers_mean:.1f} accepted answers on average (wording, units and number formats); {tags[dated]} are tagged `dated` because the amount is revised over time. Metadata give each item's source URL, the page's modification date, the date it was checked ({fetched_from}), the review votes and the licence.

## Data Collection Method

1. **Fetch and draft.** We fetched the pages ({fetched_from}) and asked {drafted_by} (temperature {generator_temperature}) for up to {max_questions_per_page} questions per page, each with an answer, variants and the passage it relies on. Page text stays local: ch.ch content may not be republished.
2. **Three blind AI reviews.** {reviewers} each judged all {candidates} candidates as keep, edit or drop against our annotation guidelines (`docs/annotation-guidelines.md`: a newcomer would ask it, it stands alone, one short answer, stated explicitly in the passage, valid in every canton, every variant correct on its own). The drafting model never reviews. Agreement: Fleiss' kappa {kappa:.3f}.
3. **Outcome rule and adjudication.** Unanimous keep: kept ({consensus[keep]}); majority drop: removed ({consensus[drop]}); everything else ({consensus[adjudicate]}) went to Claude Opus 5.5, which re-checked the passage and wrote the final item ({adjudication[edit]} edited, {adjudication[keep]} kept, {adjudication[drop]} dropped), so that one reviewer who spots an error is not outvoted.
4. **Automatic checks.** The question must be in its page's language (py3langid) and must not copy {max_copied_words} or more consecutive words from the passage; {reworded} questions were reworded.
5. **Edge cases.** Claude Opus 5.5 drafted cantonal items from the {edge[cantonal][sources]} passages that say a rule varies by canton or commune, and false-premise items from {edge[false_premise][sources]} regular items sampled evenly across topics; Claude Sonnet 5.5 reviewed each draft blind against the passage and kept {edge_items}. French has fewer cantonal items: several French passages say a rule varies "case by case", not by canton.

No human reviewed the items one by one, and no people took part as subjects; no consent was required. A consent form for future human graders is in `docs/annotator-consent-template.md`. Every vote and outcome, including the dropped candidates, is published in `review_log.jsonl`.

## Dataset Details

- **Hugging Face:** https://huggingface.co/datasets/{hf_repo} (card generated from the data, `docs/dataset_card.md`)
- **Licence:** questions, answers, metadata, responses and grades under CDLA-Permissive-2.0; each metadata line carries its licence.
- **Copyright of the source:** ch.ch text is © Swiss Federal Chancellery and is not reproduced; we publish facts, our own wording and links. The copy check above enforces this.
- **Personal data:** none; the items describe procedures, not people.
- **Files:** `test_cases.jsonl` (items), `responses.jsonl` (model responses with grades), `metadata.jsonl`, `review_log.jsonl`; the dataset card (`docs/dataset_card.md`, generated from the data) documents every field.
- **Versioning:** the Git commit of this report fixes the dataset, the recordings and the grades.

## Evaluation

### Method

Every item is asked closed-book to both models in two conditions: **swiss_context** puts "I live in Switzerland." (in the item's language) before the question, as a newcomer would; **as_asked** asks the bare question. Many questions do not name the country, and without the sentence the models often answer for another country, especially in English.

Answers are graded with SimpleQA's three-way scheme (correct / incorrect / not attempted) and its unchanged grader prompt, and we report SimpleQA's metrics: the three rates, accuracy given attempted and F1. Our first grader was Apertus 70B, the only judge on the endpoint. To check it without a human annotator, Claude Opus 5.5 and Sonnet 5.5 graded the same seeded 20% sample blind (ids hidden, no model names):

{agreement}

The two Claude graders agree with each other (kappa {a[claude-opus-5-5 vs claude-sonnet-5-5][cohen_kappa]:.2f} on the sample) far more than with the Apertus judge, which accepted answers that contradict the reference (for example "10 years" for "5 years", ages 10–20 for 8–18). The headline grades are therefore {primary}'s, applied to all responses; the Apertus judge's grades stay in the dataset for comparison and for models we have not graded offline.

### Evaluation setup and inference parameters

Answers: temperature {config.answer.temperature}, at most {config.answer.max_tokens} tokens, one sample per item and condition. Apertus judge: {config.judge.model}, temperature {config.judge.temperature}, {config.judge.max_tokens} tokens. All calls are recorded with their parameters and replayed by `make run`.

### Results

![SimpleQA outcomes by model and condition](docs/figures/outcomes.svg)

*Figure 1. Share of correct, incorrect and not-attempted answers, graded by {primary}.*

{results}

Both models answer wrongly far more often than they decline: with the country stated, the 70B model is wrong on {s[70B/swiss_context][all][all][incorrect]:.0%} of the items and declines {s[70B/swiss_context][all][all][not_attempted]:.0%}; the 8B model is wrong on {s[8B/swiss_context][all][all][incorrect]:.0%}. For a newcomer, a confident wrong deadline is worse than "I don't know".

By item kind (country stated):

{kind_results}

The two kinds of edge case split sharply. When a rule depends on the canton, the 70B model says so in {k[70B/swiss_context][kind][cantonal][correct]:.0%} of the items, but this is partly a habit: it also says a rule differs by canton in {hedge[70B]:.0%} of its replies to regular facts, which are national. When the question rests on a false premise, it rejects the premise in only {k[70B/swiss_context][kind][false_premise][correct]:.0%} and goes along with it in {k[70B/swiss_context][kind][false_premise][incorrect]:.0%} (8B: {k[8B/swiss_context][kind][false_premise][incorrect]:.0%}): a newcomer who already believes a wrong deadline or amount is likely to have it confirmed.

![Effect of stating the country](docs/figures/context_effect.svg)

*Figure 2. Correct answers per language with and without "I live in Switzerland."*

Stating the country helps the 70B model most in English, from {s[70B/as_asked][lang][en][correct]:.0%} to {s[70B/swiss_context][lang][en][correct]:.0%} correct: asked in German or French, it already assumes Switzerland; asked in English, it does not. The 8B model changes less and not in the same direction in every language (English even drops), so most of its errors are missing knowledge rather than a wrong country.

![Apertus judge versus primary grader](docs/figures/judge_leniency.svg)

*Figure 3. Incorrect answers per language as graded by {primary} and by the Apertus 70B judge.*

Graded by itself, Apertus would look much better: the judge reports {j[70B/swiss_context][all][all][incorrect]:.0%} incorrect for the 70B model instead of {s[70B/swiss_context][all][all][incorrect]:.0%}. The gap is not the same in every language: in German the judge reports {j[70B/swiss_context][lang][de][incorrect]:.0%} incorrect where {primary} finds {s[70B/swiss_context][lang][de][incorrect]:.0%}, in English {j[70B/swiss_context][lang][en][incorrect]:.0%} against {s[70B/swiss_context][lang][en][incorrect]:.0%}. With the Apertus judge, German would look like the model's strongest language; with {primary} it is its weakest, so per-language comparisons made with a self-judge are misleading.

## Dataset Limitations

- **AI-only curation and grading.** Models drafted, reviewed, adjudicated and graded the items; the agreement figures bound but do not remove shared errors. There is no human judge–grader agreement.
- **Closed-model primary grader.** Results for new models need either the same offline grading or the Apertus judge with the bias shown above.
- **Coverage.** {topics} topics; cantonal rules appear only as "it depends" edge cases, not with each canton's answer; no Romansh or Swiss German; one snapshot of the rules ({fetched_from}).
- **Contamination.** ch.ch is public and likely in Apertus's training crawl; the questions are new text but the facts are not, so the set measures recall of official public information.
- **Generator bias.** Apertus drafted the questions; the reviewers and the primary grader are a different model family.

## Lessons Learnt and Recommendations

- **Do not let the model grade itself.** The Apertus judge put the 70B model's error rate at {j[70B/swiss_context][all][all][incorrect]:.0%} instead of {s[70B/swiss_context][all][all][incorrect]:.0%}; a second, independent grader on a sample is cheap and changes the conclusion.
- **State the context the user has.** Without "I live in Switzerland" the benchmark partly measures which country the model assumes, which differs by language.
- **Next for the dataset:** more edge cases (rules that changed recently, questions ch.ch does not answer), a human check of a sample of grades, cantonal ground truth for the largest cantons, and a dated re-fetch to track rule changes.
- **For Apertus:** prefer "I don't know" or a pointer to the competent office over a guessed figure; in a Swiss deployment, assume Swiss rules in English as it already does in German and French; align with ch.ch-style official information, which is freely readable.

## Reproducibility

- **Run:** `make run` from `track_1b/` (Docker, no API key, CPU only). It replays the recorded calls in `data/recordings/`, recomputes every score from `data/dataset/responses.jsonl` and the committed grades, **fails if the result differs from `results/scores.json`**, and rewrites the dataset card, the figures and this report. `make test` runs the tests.
- **New model:** add it to `models` in `data/eval.yaml` and run `make evaluate` with `LLM_API_KEY` in `.env`; its answers are recorded and graded by the Apertus judge, and can be graded offline with the same SimpleQA rules for headline numbers.
- **Determinism:** answers and judge use temperature 0 and are replayed exactly; the dataset build (`make build-dataset`) needs the local page text, which is not redistributed.

## License

Creative Commons Attribution 4.0 (CC-BY-4.0). Code: Apache-2.0. Dataset: CDLA-Permissive-2.0.

## References

- Wei et al., *Measuring short-form factuality in large language models* (SimpleQA), 2024. https://arxiv.org/abs/2411.04368; grader prompt from https://github.com/openai/simple-evals (MIT).
- ch.ch, the Swiss authorities online. https://www.ch.ch
- Fleiss, *Measuring nominal scale agreement among many raters*, Psychological Bulletin, 1971.
- Cohen, *A coefficient of agreement for nominal scales*, Educational and Psychological Measurement, 1960.
