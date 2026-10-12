# Ailment Discoverer

An educational Python project that explores binary symptom features, Random Forest classification, input validation, dataset-quality checks, and evaluation on a small simulated dataset.

> **Important:** This is not a medical device and must not be used to diagnose, triage, or advise anyone. The dataset contains hand-written simulated records, not patient data. Model scores are not clinical probabilities.

## What the program does

- Loads a CSV with binary (`0`/`1`) feature columns and one target-label column.
- Normalizes column and symptom names, and rejects missing, non-numeric, or non-binary feature values.
- Reports singleton classes, exact duplicate records, and identical feature patterns assigned conflicting labels.
- Ranks labels using a fixed-seed, 200-tree Random Forest (single-worker for predictable runs) and displays model scores with a clear caveat.
- Evaluates the supplied data using leave-one-out cross-validation, top-1/top-3 accuracy, Wilson intervals, and a majority-class baseline.
- Includes 22 unit tests and a verification script; GitHub Actions runs the checks on pushes and pull requests.

## What the included dataset supports—and does not support

`data/simulated_symptoms.csv` has 15 records, seven binary features, and eight labels. The quality report identifies three labels with only one example, four extra exact duplicate rows, and one feature pattern assigned two different labels. These issues make performance estimates unstable and mean the model can memorize repeated patterns.

The saved metrics describe only this particular simulated dataset and evaluation procedure. They do **not** estimate real-world medical accuracy. The duplicate-removed comparison also has fewer rows, so it does not isolate the effect of duplicate records by itself. This dataset is suitable only for demonstrating coding and evaluation concepts.

## Requirements

- Python 3.10 or later
- Dependencies listed in `requirements.txt`

## Run in VS Code on Windows

Open this folder in VS Code. Select **Terminal → New Terminal**, then run the commands below from the project root.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v
.\.venv\Scripts\python.exe check.py
.\.venv\Scripts\python.exe ailment_discoverer.py --report
```

For the interactive demo:

```powershell
.\.venv\Scripts\python.exe ailment_discoverer.py
```

Or provide a comma-separated list of symptoms:

```powershell
.\.venv\Scripts\python.exe ailment_discoverer.py --symptoms "high fever, headache, skin rash"
```

To evaluate another CSV, pass its path and target column. The input must have binary numeric feature columns and one non-empty label column. A successful load does not establish that an external dataset is suitable, representative, or clinically valid.

```powershell
.\.venv\Scripts\python.exe ailment_discoverer.py --data Training.csv --target-column prognosis --report
```

## Project structure

```text
ailment-discoverer/
├── .github/workflows/checks.yml  # GitHub Actions validation
├── .vscode/                      # Test discovery and extension recommendations
├── data/
│   ├── README.md                 # Dataset provenance and caveats
│   └── simulated_symptoms.csv
├── docs/DESIGN_NOTES.md          # Evaluation choices and limitations
├── results/                      # Generated evaluation JSON and chart
├── ailment_discoverer.py         # Model, data checks, evaluation, CLI
├── test_ailment_discoverer.py    # 22 unit tests
├── check.py                     # End-to-end verification
├── requirements.txt
├── LICENSE
└── README.md
```

## Design choices and limitations

See [`docs/DESIGN_NOTES.md`](docs/DESIGN_NOTES.md) for the evaluation choices, data-quality findings, and remaining limitations. The model's score should never be described as a probability that someone has a disease. The project does not implement clinical prevalence adjustment, calibration for patient data, external validation, or safety-reviewed medical logic.

## AI assistance and authorship

AI tools were used to assist with parts of code review, refactoring, test design, debugging, and documentation. The repository owner should describe their own contributions accurately and should only claim understanding of code and results they have personally reviewed. The existence of automated tests does not replace human review.

## License

MIT License. See [`LICENSE`](LICENSE).
