# Annotation guidelines

How a drafted candidate becomes a test item. Candidates are drafted by Apertus v1.5 70B from one
ch.ch page each (`make generate`) and reviewed by a human in the review sheet (`make review-sheet`).
Nothing enters the dataset without a human decision.

## What the reviewer sees

| Column | Content |
|---|---|
| `question`, `answer`, `variants` | The draft, in the language of the source page |
| `evidence` | The ch.ch passage the draft cites (local only, never published) |
| `question_en`, `answer_en`, `evidence_en` | English machine translation, for `de` and `it` items |
| `url` | The source page |

## First pass by an AI reviewer

Before the human review, Claude (Anthropic) applied these guidelines to every candidate and wrote a
suggested decision, corrected fields, tags and a one-line reason into the `suggested_*` columns. The
human reviewer fills the decision columns independently and may copy a suggestion only after checking
it against the evidence. Agreement between the suggestions and the human decisions is reported in the
data card.

## Decision

Fill `decision` with exactly one of:

- **`keep`**: the item meets every criterion below as drafted.
- **`edit`**: the fact is a good test item but the wording, answer or variants need fixing. Write the
  corrected text in `question_fixed`, `answer_fixed`, `variants_fixed` (variants separated by ` | `).
  Leave a field empty to keep the draft's value.
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

The reviewer does not read German or Italian. These items are reviewed through the English
translation; numbers, dates and amounts are checked against the original `evidence` directly. The data
card reports which items were reviewed this way.

## Tags

Write tags in `note`, separated by commas. Tags are counted in the dataset statistics.

| Tag | Meaning |
|---|---|
| `cantonal` | The answer depends on the canton or commune; candidate for the edge-case set |
| `ambiguous` | More than one reasonable answer; drop or rewrite |
| `trivial` | Answer is implied by the question |
| `translation` | The English translation was wrong or misleading |
| `dated` | An amount or threshold that is revised over time; the verification date matters |
| `duplicate` | Same fact and evidence as another item in the same language |

## Personal data

Items must not contain personal data. ch.ch pages contain none; reject any item that does.
