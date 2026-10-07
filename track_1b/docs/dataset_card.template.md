---
license: cdla-permissive-2.0
language: [de, fr, it, en]
task_categories: [question-answering]
pretty_name: Swiss Newcomer QA
size_categories: [n<1K]
configs:
  - config_name: test_cases
    data_files: data/test_cases.jsonl
  - config_name: responses
    data_files: data/responses.jsonl
  - config_name: metadata
    data_files: data/metadata.jsonl
  - config_name: review_log
    data_files: data/review_log.jsonl
---

# Dataset Card for Swiss Newcomer QA

{items} closed-book questions in {languages} about the administrative procedures people face when they move to
Switzerland: registering with the commune, residence permits, health insurance, the AHV/AVS pension system,
withholding tax and naturalisation. Every question has a short reference answer with accepted variants, stated on a
cited page of [ch.ch](https://www.ch.ch), the federal government's information portal. {regular_items} are regular
facts that hold everywhere in Switzerland; {edge_items} are edge cases, where the answer depends on the canton or the
question rests on a false premise that a careful assistant must correct. The dataset ships with the answers of Apertus 1.5 8B and 70B and
their SimpleQA grades.

## Dataset Details

- **Curated by:** Large Canelé Model (Yumeng Ye), for the Hack Apertus 2026 Online Hack, Track 1B (Swiss Voices,
  core task intelligence)
- **Shared by:** Large Canelé Model
- **Language(s) (NLP):** German (de), French (fr), Italian (it), English (en)
- **License:** {license} for the questions, answers, metadata, model responses and grades
- **Git repository:** https://github.com/MidsummerYU/large-canele-model-apertus-1b (code to rebuild the dataset
  and rerun the evaluation)

## Uses

### Direct Use

- Closed-book evaluation of whether a language model knows Swiss administrative rules: how often it answers
  correctly, answers wrongly (hallucinates) or declines, with SimpleQA's three-way grading.
- Comparing the same model across the four languages, since every language has its own questions written from the
  same official pages.
- Evaluating retrieval-augmented assistants over ch.ch: the source URL of every item tells which page should
  have been retrieved.

### Out-of-Scope Use

- Legal or administrative advice. Rules change; the answers were checked on the dates in `source_fetched_at`.
- Cantonal or communal rules. The cantonal items only test whether a model says that a rule depends on the canton;
  the set does not contain each canton's answer.
- Training. The set is small and meant for evaluation; training on it makes later evaluations meaningless.

### Specifications

Every item passed review against the annotation guidelines (`docs/annotation-guidelines.md` in the repository):

1. a newcomer would plausibly ask it, and it names the procedure it is about;
2. it has one short factual answer (deadline, amount, age, number, office, document, yes/no);
3. the cited ch.ch passage states that answer explicitly;
4. the answer holds everywhere in Switzerland (regular items) or the page says it depends on the canton (cantonal items);
5. it is written in the language of its source page and in our own words: no {max_copied_words} or more consecutive
   words are copied from the source;
6. every accepted answer variant is correct and complete on its own.

## Dataset Structure

Composition by topic and language:

{composition}

By item kind:

{edge_composition}

- **fact** ({regular_items}): one short answer that holds everywhere in Switzerland.
- **cantonal** ({edge[cantonal][kept]}): asked as if there were one national answer, but the cited page says it depends on
  the canton or commune; the reference answer says so (with the national frame where the page gives one).
- **false_premise** ({edge[false_premise][kept]}): the question takes a wrong deadline, amount, age, obligation or office for
  granted; the reference answer rejects the premise and states the correct fact.

On average an item lists {answers_mean:.1f} accepted answers.

| File | One line per | Fields |
|---|---|---|
| `test_cases.jsonl` | test item | `item_id`, `lang`, `topic`, `question`, `answers` (first is the reference, the rest accepted variants) |
| `metadata.jsonl` | test item | `item_id`, `source_url`, `source_modified_at` (page date on ch.ch), `source_fetched_at` (date checked), `source_publisher`, `license`, `tags`, `drafted_by`, `review_votes`, `adjudicated`, `final_decision`, `question_reworded` |
| `responses.jsonl` | model × condition × item | `item_id`, `lang`, `topic`, `model`, `condition`, `response`, `grade` ({primary}), `judge_grade` (Apertus judge), `judge_output` |
| `review_log.jsonl` | drafted candidate, kept or not | `candidate_id`, `lang`, `topic`, `source_url`, `review_votes`, `consensus`, `adjudication`, `in_dataset` |

There is no train/test split: the whole set is a test set. Items in different languages that come from parallel
pages of the same topic are independent questions, not translations of each other.

## Dataset Creation

### Curation Rationale

Newcomers to Switzerland meet a dense set of procedures with short deadlines, often before they speak a national
language well, and increasingly ask chatbots. A sovereign Swiss model should know these rules in every national
language and in English, and should say so when it does not know. Existing Swiss benchmarks focus on law and
legal reasoning (for example LEXam); this set tests the practical rules that ch.ch explains to residents.

### Source Data

{pages} pages of ch.ch: one German seed page per subject listed in `data/sources.yaml`, plus its official parallel
pages in French, Italian and English found through the site's language switcher. The pages were last modified on
ch.ch between {modified_from} and {modified_to}.

#### Data Collection

1. **Fetch** (`make fetch`, {fetched_from} to {fetched_to}): page text and the page's modification date. Page text is
   kept locally and never published.
2. **Draft** (`make generate`): {drafted_by}, temperature {generator_temperature}, writes up to {max_questions_per_page}
   questions per page, each with an answer, variants and the passage it relies on, in the page's language.
3. **Review and build**: see *Data Processing and Quality Control*.

#### Source Data Producers and Data Subjects

ch.ch is edited by the Swiss Federal Chancellery with the federal offices and the cantons. The pages describe
procedures, not people: there are no data subjects.

#### Ownership and Consent Management

- **Source text.** ch.ch content is © Swiss Federal Chancellery, and reproduction needs prior written consent. We
  therefore publish no ch.ch text: only facts (which are not protected), questions and answers in our own wording,
  checked automatically for copied runs of {max_copied_words}+ words, and links to the pages.
- **Our content.** The questions, answers, metadata and grades were produced by AI models under our direction and
  are released by the team under {license}. Apertus 1.5 is Apache-2.0; Claude was used under Anthropic's terms of
  service.
- **Consent.** No people took part and no personal data was collected, so no consent was needed. For a future human
  check of the grades, `docs/annotator-consent-template.md` in the repository is the consent form we would use.
- **AI permissions.** The data may be used to evaluate and improve AI systems; using it as training data is out of
  scope (see above), not forbidden.

#### Data Processing and Quality Control

1. **Three blind AI reviews.** {reviewers} each judged every one of the {candidates} drafted candidates as keep, edit
   or drop against the guidelines and the source passage, without seeing each other. The model that drafted an
   item never reviews it. Agreement over keep/edit/drop: Fleiss' kappa {kappa:.3f}.
2. **Outcome rule.** Unanimous keep: kept as drafted ({consensus[keep]}). Majority drop: removed ({consensus[drop]}).
   Anything else goes to adjudication ({consensus[adjudicate]}), so that one reviewer who spots a real error is not
   outvoted.
3. **Adjudication.** Claude Opus 5.5 re-checked each disputed item against the passage and wrote the final question
   and answers: {adjudication[edit]} edited, {adjudication[keep]} kept, {adjudication[drop]} dropped.
4. **Automatic checks** (`make build-dataset`): the question must be in its page's language (py3langid), and must not
   copy {max_copied_words}+ consecutive words from the passage; {reworded} questions were reworded for the second check.
5. **Result.** {items} items; {tags[dated]} are tagged `dated` (amounts that are revised over time).

6. **Edge cases.** Claude Opus 5.5 drafted one cantonal item for each of the {edge[cantonal][sources]} passages that say a
   rule varies by canton or commune (it skipped {edge[cantonal][skipped]} where the variation is not by canton or not
   something a newcomer asks), and one false-premise item for each of {edge[false_premise][sources]} regular items sampled
   evenly across topics (skipped {edge[false_premise][skipped]}). Claude Sonnet 5.5 reviewed every draft blind against the
   passage with stricter rules (every statement of the answer stated explicitly, the premise clearly false yet
   plausible) and dropped {edge[cantonal][dropped]} cantonal and {edge[false_premise][dropped]} false-premise drafts. The same
   language and copy checks apply. French has fewer cantonal items because several French passages say a rule varies
   "case by case", not by canton.

`review_log.jsonl` records every vote and outcome, including the dropped candidates. **No item was reviewed one by
one by a human.**

#### Data Instance Licenses

Every line of `metadata.jsonl` carries `license` ({license}), the `source_url` it was checked against and a
`source_publisher` note that ch.ch is the source of the facts and that no text is reproduced.

### Annotations

The annotations are the reference answers with their variants (from the review above) and the grades of the model
responses.

#### Annotation Process

Each test item is asked closed-book, without a system prompt, to {config.models[8B]} and {config.models[70B]}
(temperature {config.answer.temperature}, up to {config.answer.max_tokens} tokens) in two conditions: `swiss_context`
puts a sentence saying the user lives in Switzerland before the question, in the item's language; `as_asked` asks the
bare question. Many questions do not name the country, and without that sentence the models often answer for
another country.

Grades follow SimpleQA (correct / incorrect / not attempted) with its unchanged grader prompt:

- **{primary}** grades every response (the `grade` field), on blinded and shuffled items without model names. As in
  SimpleQA, an answer that neither confirms nor contradicts the reference (e.g. a range around it) is not attempted.
- **Apertus 1.5 70B** grades every response inside the evaluation harness (`judge_grade`), the only judge available
  on the hackathon endpoint.
- **Claude Sonnet 5.5** independently grades a seeded random 20% of the `swiss_context` responses of each item
  kind.
- For the edge cases, both Claude graders also received the paragraph in `data/grader/edge_addendum.txt`, which says
  how an "it depends" or a correction counts; the Apertus judge uses the unchanged prompt for every item.

{agreement}

The two Claude graders agree closely; the Apertus judge accepts answers that contradict the reference, which is why
the primary grades come from {primary}.

#### Annotator Details

All drafters, reviewers, adjudicators and graders are AI models: Claude Opus 5.5, Claude Sonnet 5.5 and Claude Fable 5.1
(Anthropic), and Apertus 1.5 70B (Swiss AI Initiative). The guidelines, the outcome rule and the grading setup were
written by the team with an AI coding assistant.

## Evaluation Results

Regular fact items ({regular_items}), graded by {primary}:

{results}

By item kind, in the `{config.main_condition}` condition:

{kind_results}

Regular fact items graded by the Apertus 70B judge, for comparison:

{judge_results}

With the country stated, Apertus 1.5 70B answers {s[70B/swiss_context][all][all][incorrect]:.0%} of the questions
incorrectly and declines only {s[70B/swiss_context][all][all][not_attempted]:.0%}; its own judge reports
{j[70B/swiss_context][all][all][incorrect]:.0%} incorrect.

## Risks, Bias, and Limitations

- **AI-only curation.** Drafting, review, adjudication and grading are all done by models. Errors that every model
  shares can survive; the agreement figures above bound, but do not remove, that risk.
- **Generator bias.** Apertus drafted the questions, which may favour phrasings it finds easy. The reviewers and the
  primary grader are a different model family.
- **Closed-model grader.** The headline grades come from a proprietary model; the Apertus judge grades are included
  so that results can be recomputed with an open model.
- **Time.** Amounts and thresholds change; check `source_fetched_at` and the `dated` tag before reusing an item.
- **Contamination.** ch.ch is public and very likely part of web crawls used to train Apertus. The questions are new
  text, but the facts are not: the set measures recall of public official information, not reasoning on unseen facts.
- **Coverage.** {topics} topics and {pages} pages; no cantonal rules, no Romansh, no Swiss German.

### Personally Identifiable Information

None. The items describe procedures, contain no names of individuals, and the model responses are about those
procedures only.

### Sensitive Information

The topics include residence status, nationality and health insurance, but no item refers to a person.

### Recommendations

Report the three SimpleQA rates, not accuracy alone: a model that declines when unsure is safer for newcomers than
one that answers wrongly. Treat the results as a snapshot of the rules on the fetch dates.

## Citations

**BibTeX:**

```bibtex
@misc{{swiss_newcomer_qa_2026,
  title  = {{Swiss Newcomer QA: closed-book questions on Swiss administrative procedures}},
  author = {{Large Canelé Model}},
  year   = {{2026}},
  note   = {{Hack Apertus 2026, Track 1B}},
  url    = {{https://github.com/MidsummerYU/large-canele-model-apertus-1b}}
}}
```

**APA:** Large Canelé Model. (2026). *Swiss Newcomer QA: closed-book questions on Swiss administrative procedures*
[Data set]. Hack Apertus 2026, Track 1B.

## Dataset Card Authors

Large Canelé Model (Yumeng Ye)

## Dataset Card Contact

Issues on the Git repository above.
