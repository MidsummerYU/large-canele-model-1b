# Closed-book results

SimpleQA grading by the judge in data/eval.yaml.

## Grader agreement on the sample

| comparison | n | agreement | Cohen's kappa |
|---|---|---|---|
| judge vs claude-opus-5-5 | 132 | 68.9% | 0.491 |
| judge vs claude-sonnet-5-5 | 132 | 72.0% | 0.528 |
| claude-opus-5-5 vs claude-sonnet-5-5 | 132 | 93.2% | 0.885 |

## Overall

| model/condition | group | n | correct | incorrect | not attempted | correct given attempted | F1 |
|---|---|---|---|---|---|---|---|
| 8B/swiss_context | all | 329 | 55.3% | 23.4% | 21.3% | 70.3% | 0.619 |
| 70B/swiss_context | all | 329 | 69.6% | 13.1% | 17.3% | 84.2% | 0.762 |
| 8B/as_asked | all | 329 | 48.3% | 30.4% | 21.3% | 61.4% | 0.541 |
| 70B/as_asked | all | 329 | 61.7% | 18.8% | 19.5% | 76.6% | 0.684 |

## By lang

| model/condition | group | n | correct | incorrect | not attempted | correct given attempted | F1 |
|---|---|---|---|---|---|---|---|
| 8B/swiss_context | de | 82 | 50.0% | 31.7% | 18.3% | 61.2% | 0.550 |
| 8B/swiss_context | en | 84 | 50.0% | 25.0% | 25.0% | 66.7% | 0.571 |
| 8B/swiss_context | fr | 80 | 56.2% | 21.2% | 22.5% | 72.6% | 0.634 |
| 8B/swiss_context | it | 83 | 65.1% | 15.7% | 19.3% | 80.6% | 0.720 |
| 70B/swiss_context | de | 82 | 75.6% | 11.0% | 13.4% | 87.3% | 0.810 |
| 70B/swiss_context | en | 84 | 60.7% | 16.7% | 22.6% | 78.5% | 0.685 |
| 70B/swiss_context | fr | 80 | 70.0% | 13.8% | 16.2% | 83.6% | 0.762 |
| 70B/swiss_context | it | 83 | 72.3% | 10.8% | 16.9% | 87.0% | 0.789 |
| 8B/as_asked | de | 82 | 47.6% | 40.2% | 12.2% | 54.2% | 0.506 |
| 8B/as_asked | en | 84 | 42.9% | 21.4% | 35.7% | 66.7% | 0.522 |
| 8B/as_asked | fr | 80 | 50.0% | 37.5% | 12.5% | 57.1% | 0.533 |
| 8B/as_asked | it | 83 | 53.0% | 22.9% | 24.1% | 69.8% | 0.603 |
| 70B/as_asked | de | 82 | 69.5% | 15.9% | 14.6% | 81.4% | 0.750 |
| 70B/as_asked | en | 84 | 46.4% | 16.7% | 36.9% | 73.6% | 0.569 |
| 70B/as_asked | fr | 80 | 71.2% | 18.8% | 10.0% | 79.2% | 0.750 |
| 70B/as_asked | it | 83 | 60.2% | 24.1% | 15.7% | 71.4% | 0.654 |

## By topic

| model/condition | group | n | correct | incorrect | not attempted | correct given attempted | F1 |
|---|---|---|---|---|---|---|---|
| 8B/swiss_context | health_insurance | 58 | 53.4% | 19.0% | 27.6% | 73.8% | 0.620 |
| 8B/swiss_context | naturalisation | 30 | 26.7% | 26.7% | 46.7% | 50.0% | 0.348 |
| 8B/swiss_context | pension | 90 | 57.8% | 23.3% | 18.9% | 71.2% | 0.638 |
| 8B/swiss_context | registration | 25 | 52.0% | 28.0% | 20.0% | 65.0% | 0.578 |
| 8B/swiss_context | residence_permit | 90 | 56.7% | 26.7% | 16.7% | 68.0% | 0.618 |
| 8B/swiss_context | withholding_tax | 36 | 75.0% | 16.7% | 8.3% | 81.8% | 0.783 |
| 70B/swiss_context | health_insurance | 58 | 69.0% | 10.3% | 20.7% | 87.0% | 0.769 |
| 70B/swiss_context | naturalisation | 30 | 56.7% | 13.3% | 30.0% | 81.0% | 0.667 |
| 70B/swiss_context | pension | 90 | 72.2% | 14.4% | 13.3% | 83.3% | 0.774 |
| 70B/swiss_context | registration | 25 | 44.0% | 28.0% | 28.0% | 61.1% | 0.512 |
| 70B/swiss_context | residence_permit | 90 | 75.6% | 11.1% | 13.3% | 87.2% | 0.810 |
| 70B/swiss_context | withholding_tax | 36 | 77.8% | 8.3% | 13.9% | 90.3% | 0.836 |
| 8B/as_asked | health_insurance | 58 | 48.3% | 20.7% | 31.0% | 70.0% | 0.571 |
| 8B/as_asked | naturalisation | 30 | 23.3% | 33.3% | 43.3% | 41.2% | 0.298 |
| 8B/as_asked | pension | 90 | 50.0% | 32.2% | 17.8% | 60.8% | 0.549 |
| 8B/as_asked | registration | 25 | 36.0% | 52.0% | 12.0% | 40.9% | 0.383 |
| 8B/as_asked | residence_permit | 90 | 50.0% | 31.1% | 18.9% | 61.6% | 0.552 |
| 8B/as_asked | withholding_tax | 36 | 69.4% | 22.2% | 8.3% | 75.8% | 0.725 |
| 70B/as_asked | health_insurance | 58 | 60.3% | 10.3% | 29.3% | 85.4% | 0.707 |
| 70B/as_asked | naturalisation | 30 | 43.3% | 30.0% | 26.7% | 59.1% | 0.500 |
| 70B/as_asked | pension | 90 | 65.6% | 16.7% | 17.8% | 79.7% | 0.720 |
| 70B/as_asked | registration | 25 | 48.0% | 32.0% | 20.0% | 60.0% | 0.533 |
| 70B/as_asked | residence_permit | 90 | 63.3% | 20.0% | 16.7% | 76.0% | 0.691 |
| 70B/as_asked | withholding_tax | 36 | 75.0% | 16.7% | 8.3% | 81.8% | 0.783 |
