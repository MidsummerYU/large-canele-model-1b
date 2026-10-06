# Closed-book results

SimpleQA grades by `claude-opus-5-5` (see data/eval.yaml).

## Grader agreement

| comparison | n | agreement | Cohen's kappa |
|---|---|---|---|
| judge vs claude-opus-5-5 | 1316 | 71.7% | 0.541 |
| judge vs claude-sonnet-5-5 | 132 | 72.0% | 0.528 |
| claude-opus-5-5 vs claude-sonnet-5-5 | 132 | 93.2% | 0.885 |

## Overall as graded by the in-harness Apertus judge, for comparison

| model/condition | correct | incorrect | not attempted | correct given attempted | F1 |
|---|---|---|---|---|---|
| 8B/swiss_context | 55.3% | 23.4% | 21.3% | 70.3% | 0.619 |
| 70B/swiss_context | 69.6% | 13.1% | 17.3% | 84.2% | 0.762 |
| 8B/as_asked | 48.3% | 30.4% | 21.3% | 61.4% | 0.541 |
| 70B/as_asked | 61.7% | 18.8% | 19.5% | 76.6% | 0.684 |

## Overall

| model/condition | group | n | correct | incorrect | not attempted | correct given attempted | F1 |
|---|---|---|---|---|---|---|---|
| 8B/swiss_context | all | 329 | 41.6% | 48.0% | 10.3% | 46.4% | 0.439 |
| 70B/swiss_context | all | 329 | 55.6% | 38.9% | 5.5% | 58.8% | 0.572 |
| 8B/as_asked | all | 329 | 38.0% | 46.2% | 15.8% | 45.1% | 0.413 |
| 70B/as_asked | all | 329 | 46.2% | 44.1% | 9.7% | 51.2% | 0.486 |

## By lang

| model/condition | group | n | correct | incorrect | not attempted | correct given attempted | F1 |
|---|---|---|---|---|---|---|---|
| 8B/swiss_context | de | 82 | 36.6% | 57.3% | 6.1% | 39.0% | 0.377 |
| 8B/swiss_context | en | 84 | 33.3% | 53.6% | 13.1% | 38.4% | 0.357 |
| 8B/swiss_context | fr | 80 | 43.8% | 45.0% | 11.2% | 49.3% | 0.464 |
| 8B/swiss_context | it | 83 | 53.0% | 36.1% | 10.8% | 59.5% | 0.561 |
| 70B/swiss_context | de | 82 | 48.8% | 45.1% | 6.1% | 51.9% | 0.503 |
| 70B/swiss_context | en | 84 | 59.5% | 36.9% | 3.6% | 61.7% | 0.606 |
| 70B/swiss_context | fr | 80 | 56.2% | 38.8% | 5.0% | 59.2% | 0.577 |
| 70B/swiss_context | it | 83 | 57.8% | 34.9% | 7.2% | 62.3% | 0.600 |
| 8B/as_asked | de | 82 | 32.9% | 57.3% | 9.8% | 36.5% | 0.346 |
| 8B/as_asked | en | 84 | 35.7% | 36.9% | 27.4% | 49.2% | 0.414 |
| 8B/as_asked | fr | 80 | 40.0% | 50.0% | 10.0% | 44.4% | 0.421 |
| 8B/as_asked | it | 83 | 43.4% | 41.0% | 15.7% | 51.4% | 0.471 |
| 70B/as_asked | de | 82 | 42.7% | 47.6% | 9.8% | 47.3% | 0.449 |
| 70B/as_asked | en | 84 | 41.7% | 41.7% | 16.7% | 50.0% | 0.455 |
| 70B/as_asked | fr | 80 | 51.2% | 45.0% | 3.8% | 53.2% | 0.522 |
| 70B/as_asked | it | 83 | 49.4% | 42.2% | 8.4% | 53.9% | 0.516 |

## By topic

| model/condition | group | n | correct | incorrect | not attempted | correct given attempted | F1 |
|---|---|---|---|---|---|---|---|
| 8B/swiss_context | health_insurance | 58 | 43.1% | 51.7% | 5.2% | 45.5% | 0.442 |
| 8B/swiss_context | naturalisation | 30 | 20.0% | 40.0% | 40.0% | 33.3% | 0.250 |
| 8B/swiss_context | pension | 90 | 42.2% | 47.8% | 10.0% | 46.9% | 0.444 |
| 8B/swiss_context | registration | 25 | 40.0% | 40.0% | 20.0% | 50.0% | 0.444 |
| 8B/swiss_context | residence_permit | 90 | 43.3% | 51.1% | 5.6% | 45.9% | 0.446 |
| 8B/swiss_context | withholding_tax | 36 | 52.8% | 47.2% | 0.0% | 52.8% | 0.528 |
| 70B/swiss_context | health_insurance | 58 | 51.7% | 43.1% | 5.2% | 54.5% | 0.531 |
| 70B/swiss_context | naturalisation | 30 | 33.3% | 40.0% | 26.7% | 45.5% | 0.385 |
| 70B/swiss_context | pension | 90 | 56.7% | 37.8% | 5.6% | 60.0% | 0.583 |
| 70B/swiss_context | registration | 25 | 48.0% | 52.0% | 0.0% | 48.0% | 0.480 |
| 70B/swiss_context | residence_permit | 90 | 64.4% | 34.4% | 1.1% | 65.2% | 0.648 |
| 70B/swiss_context | withholding_tax | 36 | 61.1% | 36.1% | 2.8% | 62.9% | 0.620 |
| 8B/as_asked | health_insurance | 58 | 41.4% | 36.2% | 22.4% | 53.3% | 0.466 |
| 8B/as_asked | naturalisation | 30 | 20.0% | 53.3% | 26.7% | 27.3% | 0.231 |
| 8B/as_asked | pension | 90 | 37.8% | 47.8% | 14.4% | 44.2% | 0.407 |
| 8B/as_asked | registration | 25 | 28.0% | 56.0% | 16.0% | 33.3% | 0.304 |
| 8B/as_asked | residence_permit | 90 | 37.8% | 48.9% | 13.3% | 43.6% | 0.405 |
| 8B/as_asked | withholding_tax | 36 | 55.6% | 38.9% | 5.6% | 58.8% | 0.571 |
| 70B/as_asked | health_insurance | 58 | 44.8% | 43.1% | 12.1% | 51.0% | 0.477 |
| 70B/as_asked | naturalisation | 30 | 26.7% | 53.3% | 20.0% | 33.3% | 0.296 |
| 70B/as_asked | pension | 90 | 48.9% | 43.3% | 7.8% | 53.0% | 0.509 |
| 70B/as_asked | registration | 25 | 36.0% | 56.0% | 8.0% | 39.1% | 0.375 |
| 70B/as_asked | residence_permit | 90 | 51.1% | 41.1% | 7.8% | 55.4% | 0.532 |
| 70B/as_asked | withholding_tax | 36 | 52.8% | 38.9% | 8.3% | 57.6% | 0.551 |
