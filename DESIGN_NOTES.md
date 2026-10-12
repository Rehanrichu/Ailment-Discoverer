# Design notes

## Purpose

This repository is a small learning exercise in tabular classification, data validation, input handling, and evaluation. It is not a medical system.

## Dataset audit

The included CSV has 15 simulated rows, seven binary symptom features, and eight labels. An audit of the supplied file identifies:

- Three labels with only one row each.
- Four extra exact duplicate records (same feature values and same label).
- One symptom pattern associated with two different labels.

These are properties of the included file, not claims about real disease data.

## Evaluation

Leave-one-out cross-validation is used because this example has very few rows. Each row is predicted by a model fitted without that row. Top-1 and top-3 accuracy are reported with Wilson intervals and compared with the majority-class baseline.

These intervals quantify uncertainty under this evaluation setup; they do not correct for the tiny, hand-written dataset, duplicate records, conflicting labels, or unrepresentative class distribution. When a held-out label is absent from a training fold, the fitted classifier cannot predict that label. This is a dataset limitation and should not be hidden.

Exact duplicates are also evaluated after removal for demonstration. That comparison changes the data size and class counts, so it is not a controlled experiment isolating duplication alone.

## Model scores

Random Forest `predict_proba` scores are printed as model scores only. They have not been validated or calibrated as clinical probabilities. Ranking labels is not equivalent to making a diagnosis.

## Known limitations / next responsible steps

- The only bundled data is synthetic and tiny.
- Labels and symptom patterns were manually assembled, not clinically reviewed.
- No claim is made about generalization to real people or another dataset.
- A real health application would require appropriate data governance, qualified clinical review, external evaluation, calibration, safety design, and compliance review. Those elements are outside the scope of this project.
