# Annotation guidelines

How a drafted candidate becomes a test item. Candidates are drafted by Apertus v1.5 70B from one
ch.ch page each (`make generate`). Each candidate is then reviewed against these guidelines by three
independent AI reviewers, and disagreements are adjudicated (see *Review process*). No item was
reviewed one by one by a human.

## What the reviewer sees

| Column | Content |
|---|---|
| `question`, `answer`, `variants` | The draft, in the language of the source page |
| `evidence` | The ch.ch passage the draft cites (local only, never published) |
| `question_en`, `answer_en`, `evidence_en` | English machine translation, for `de` and `it` items |
| `url` | The source page |

## Review process

1. **Three blind reviews.** Claude Opus 5.5, Claude Sonnet 5.5 and Claude Fable 5.1 each reviewed every
   candidate with these guidelines, without seeing the other reviews. Reviewers other than the
   generator were chosen so that the model that wrote an item never judges it.
2. **Outcome rule** (`make consensus`): unanimous `keep` keeps the draft; a majority of `drop` removes
   the item; everything else goes to adjudication, so that one reviewer who spots a real error is not
   outvoted. Agreement is reported as Fleiss' kappa over keep/edit/drop.
3. **Adjudication.** Claude Opus 5.5 sees the draft, the evidence and the three reviews, re-checks the
   evidence itself and writes the complete final question, answers and tags.
4. **Automatic checks** (`make build-dataset`): the question must be in the language of its source
   page, and must not share 8 or more consecutive words with the source passage. Questions that fail
   the second check are reworded and flagged `question_reworded` in the metadata.

## Decision

Each reviewer chooses exactly one of:

- **`keep`**: the item meets every criterion below as drafted.
- **`edit`**: the fact is a good test item but the wording, answer or variants need fixing. Give the
  corrected question, answer and variants (variants separated by ` | `); a field left empty keeps the
  draft's value.
- **`drop`**: the item cannot be fixed by rewording.

## Criteria for a question

1. **A newcomer would ask it.** It concerns a procedure, permit, insurance, tax or deadline that people
   who move to Switzerland deal with. Drop trivia and tautologies ("Who submits the application?" →
   "The applicant").
2. **It stands alone.** It names the procedure it is about and makes sense without the page.
3. **It has one short, factual answer**: a deadline, amount, age, number, office, document or yes/no.
4. **The evidence states the answer explicitly.** Do not accept answers that need outside knowledge or
   an inference the passage does not make.
5. **The answer holds everywhere in Switzerland.** If the passage says it depends on the canton or the
   commune, do not keep it as a regular item: tag it `cantonal` (see below).
6. **It is phrased in our own words**, not a sentence copied from the page.

## Criteria for answers and variants

- The `answer` is the shortest complete correct answer.
- **Every variant must be correct and complete on its own.** Remove variants that cover only part of
  the answer or change its meaning (e.g. "at the latest two weeks before expiry" is not "within two
  weeks of expiry").
- Variants may differ in wording, units or number format ("14 days", "two weeks", "14 Tage").

## Items in German and Italian

The review sheet adds an English machine translation for `de` and `it` items as an aid. The AI
reviewers read the original question, answer and evidence; the translation is never the reference.

## Tags

Write tags in `note`, separated by commas. Tags are counted in the dataset statistics.

| Tag | Meaning |
|---|---|
| `cantonal` | The answer depends on the canton or commune; candidate for the edge-case set |
| `ambiguous` | More than one reasonable answer; drop or rewrite |
| `trivial` | Answer is implied by the question |
| `dated` | An amount or threshold that is revised over time; the verification date matters |
| `duplicate` | Same fact and evidence as another item in the same language |

## Personal data

Items must not contain personal data. ch.ch pages contain none; reject any item that does.
