"""Ailment Discoverer: an educational symptom-pattern classification demo.

This program trains a Random Forest on a small, hand-written simulated dataset.
It is not a medical tool and must not be used to diagnose, triage, or advise anyone.
The optional CSV loader accepts numeric 0/1 feature columns and one label column;
other datasets still require schema review and independent validation.

Examples (run from this folder):
    python ailment_discoverer.py --report
    python ailment_discoverer.py
    python ailment_discoverer.py --symptoms "high fever, cough"
    python ailment_discoverer.py --data Training.csv --target-column prognosis --report
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from math import sqrt
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold, LeaveOneOut, StratifiedKFold

DEFAULT_DATA = Path(__file__).resolve().parent / "data" / "simulated_symptoms.csv"
SEED = 42

DISCLAIMER = (
    "This is an educational machine-learning demo, not a medical device. It cannot diagnose "
    "anything. If you feel seriously unwell, have trouble breathing, chest pain, confusion or "
    "symptoms that are getting worse, seek medical care immediately."
)


# ------------------------------------------------------------------------------- data
def normalize_name(name: object) -> str:
    """'Skin Rash', ' skin _rash' and 'skin_rash' all become 'skin_rash'.
    Real-world CSVs often contain stray spaces in column names."""
    return re.sub(r"[\s_]+", "_", str(name).strip().lower()).strip("_")


def load_dataset(
    path: str | Path | None = None,
    target_column: str = "disease",
) -> tuple[pd.DataFrame, pd.Series]:
    """Load and validate a CSV with binary symptom features and a label column.

    Blank symptoms and labels are rejected rather than silently interpreted as
    negative symptoms or converted to the string "nan".
    """
    source = Path(path) if path is not None else DEFAULT_DATA
    try:
        df = pd.read_csv(source)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"Dataset is empty: {source}") from exc
    except FileNotFoundError:
        raise

    if df.empty:
        raise ValueError("Dataset has no data rows.")

    # Ignore only common empty index columns created by spreadsheet exports.
    unnamed = df.columns.astype(str).str.strip().str.casefold().str.startswith("unnamed")
    df = df.loc[:, ~unnamed].copy()
    if df.shape[1] == 0:
        raise ValueError("Dataset has no usable columns.")

    cleaned = [normalize_name(column) for column in df.columns]
    collisions = sorted({name for name in cleaned if cleaned.count(name) > 1})
    if collisions:
        raise ValueError(f"Column names collide after cleaning: {collisions[:5]}")
    df.columns = cleaned

    target_name = normalize_name(target_column)
    if target_name not in df.columns:
        raise ValueError(
            f"Target column '{target_name}' not found. Available columns: {list(df.columns)}"
        )

    labels = df[target_name]
    blank_labels = labels.isna() | labels.astype("string").str.strip().eq("")
    if blank_labels.any():
        raise ValueError("Target column contains missing or blank labels.")

    X = df.drop(columns=target_name).copy()
    if X.shape[1] == 0:
        raise ValueError("Dataset must contain at least one symptom feature column.")

    for column in X.columns:
        original = X[column]
        numeric = pd.to_numeric(original, errors="coerce")
        invalid_text = original.notna() & numeric.isna()
        if invalid_text.any():
            raise ValueError(f"Symptom column '{column}' contains non-numeric values.")
        if numeric.isna().any():
            raise ValueError(
                f"Symptom column '{column}' contains missing values. "
                "Resolve them explicitly; missing is not the same as 'No'."
            )
        if not numeric.isin([0, 1]).all():
            raise ValueError(f"Symptom column '{column}' must contain only 0/1 values.")
        X[column] = numeric.astype(int)

    return X, labels.astype(str).str.strip().rename(target_name)


def data_quality_report(X: pd.DataFrame, y: pd.Series) -> dict:
    """Problems that make accuracy numbers unreliable, found before any model is trained."""
    counts = y.value_counts()
    profile = X.assign(_label=y.to_numpy())
    labels_per_profile = profile.groupby(list(X.columns))["_label"].nunique()
    report = {
        "n_rows": int(len(X)),
        "n_symptoms": int(X.shape[1]),
        "n_diseases": int(len(counts)),
        "rows_per_disease_min": int(counts.min()),
        "rows_per_disease_max": int(counts.max()),
        "diseases_with_a_single_row": sorted(counts[counts == 1].index.tolist()),
        "exact_duplicate_rows": int(profile.duplicated().sum()),
        "symptom_profiles_with_conflicting_labels": int((labels_per_profile > 1).sum()),
    }
    notes = []
    if report["n_rows"] < 100:
        notes.append("Fewer than 100 rows: any accuracy estimate will have a very wide confidence interval.")
    if report["diseases_with_a_single_row"]:
        notes.append("Diseases with one example cannot be learned or tested fairly (nothing left to train on "
                     "once that row is held out).")
    if report["exact_duplicate_rows"]:
        notes.append("Exact duplicate rows leak between training and test sets and inflate accuracy.")
    if report["symptom_profiles_with_conflicting_labels"]:
        notes.append("Identical symptom patterns carry different disease labels; no model can get both right.")
    report["warnings"] = notes
    return report


# ------------------------------------------------------------------------------ model
def build_model(seed: int = SEED) -> RandomForestClassifier:
    """Build a deterministic, single-worker Random Forest for the demo."""
    return RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=1)


def rank_diagnoses(model: RandomForestClassifier, symptoms: pd.DataFrame, top_k: int = 3) -> list[tuple[str, float]]:
    """Rank known labels by model score; scores are not clinical probabilities."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")
    scores = model.predict_proba(symptoms)[0]
    order = np.argsort(scores)[::-1][:top_k]
    return [(str(model.classes_[i]), float(scores[i])) for i in order if scores[i] > 0]


def deduplicate(X: pd.DataFrame, y: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """Drop exact duplicate rows (same symptoms AND same label)."""
    df = X.assign(_label=y.to_numpy()).drop_duplicates()
    return df.drop(columns="_label").reset_index(drop=True), pd.Series(df["_label"].to_numpy(), name=y.name)


# --------------------------------------------------------------------------- evaluate
def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Return a Wilson score interval for k successes in n trials."""
    if n <= 0:
        raise ValueError("n must be greater than zero.")
    if k < 0 or k > n:
        raise ValueError("k must be between zero and n.")
    if z <= 0:
        raise ValueError("z must be greater than zero.")
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (round(centre - half, 3), round(centre + half, 3))


def evaluate(X: pd.DataFrame, y: pd.Series, seed: int = SEED) -> dict:
    """Out-of-sample top-1 / top-3 accuracy with 95% Wilson intervals.

    Leave-one-out for tiny data, stratified 5-fold otherwise. Every row is predicted by a model
    that never saw it.
    """
    n = len(X)
    if n < 2:
        raise ValueError("At least two rows are required for out-of-sample evaluation.")
    if len(y) != n:
        raise ValueError("X and y must contain the same number of rows.")
    if n <= 60:
        splitter, method = LeaveOneOut(), "leave-one-out"
        splits = splitter.split(X)
    elif y.value_counts().min() >= 5:
        splitter, method = StratifiedKFold(5, shuffle=True, random_state=seed), "stratified 5-fold"
        splits = splitter.split(X, y)
    else:
        splitter, method = KFold(5, shuffle=True, random_state=seed), "5-fold"
        splits = splitter.split(X)

    top1 = top3 = 0
    for train_idx, test_idx in splits:
        model = build_model(seed).fit(X.iloc[train_idx], y.iloc[train_idx])
        proba = model.predict_proba(X.iloc[test_idx])
        for row, truth in zip(proba, y.iloc[test_idx]):
            ranked = model.classes_[np.argsort(row)[::-1]]
            top1 += int(ranked[0] == truth)
            top3 += int(truth in ranked[:3])  # a disease unseen in training can never be ranked
    return {
        "method": method, "n": n,
        "top1_accuracy": round(top1 / n, 3), "top1_ci95": wilson_interval(top1, n),
        "top3_accuracy": round(top3 / n, 3), "top3_ci95": wilson_interval(top3, n),
        "majority_class_baseline": round(float(y.value_counts(normalize=True).iloc[0]), 3),
    }


def plot_evaluation(groups: dict[str, dict], path: Path) -> None:
    """Bar chart of top-1 / top-3 accuracy with 95% CIs and the guess-the-commonest baseline.
    Silently skipped if matplotlib is not installed (it is only needed for this figure)."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    width = 0.34
    for i, (name, r) in enumerate(groups.items()):
        for j, (key, colour, label) in enumerate([("top1", "#3b6ea5", "top-1"), ("top3", "#e4572e", "top-3")]):
            acc, (lo, hi) = r[f"{key}_accuracy"], r[f"{key}_ci95"]
            ax.bar(i + (j - 0.5) * width, acc, width, color=colour, label=label if i == 0 else None,
                   yerr=[[acc - lo], [hi - acc]], capsize=4)
        ax.hlines(r["majority_class_baseline"], i - 0.4, i + 0.4, colors="k", linestyles="--",
                  label="always guess the commonest disease" if i == 0 else None)
    ax.set_xticks(range(len(groups)), [f"{n}\n(n={r['n']})" for n, r in groups.items()])
    ax.set(ylim=(0, 1.05), ylabel="Out-of-sample accuracy (95% CI)", title="Out-of-sample model evaluation")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ----------------------------------------------------------------------- user input
YES, NO = {"1", "y", "yes", "true"}, {"0", "n", "no", "false"}


def parse_yes_no(text: str) -> int:
    t = text.strip().lower()
    if t in YES:
        return 1
    if t in NO:
        return 0
    raise ValueError("Please answer y/n (or 1/0).")


def parse_symptom_list(text: str, columns: Iterable[str]) -> list[str]:
    """'High fever, cough' -> ['high_fever', 'cough'] with helpful errors for typos."""
    columns = list(columns)
    chosen = []
    for raw in text.split(","):
        name = normalize_name(raw)
        if not name:
            continue
        if name not in columns:
            hint = difflib.get_close_matches(name, columns, n=3)
            suffix = f" Did you mean: {', '.join(hint)}?" if hint else ""
            raise ValueError(f"Unknown symptom '{raw.strip()}'.{suffix}")
        if name not in chosen:
            chosen.append(name)
    return chosen


def vector_from_symptoms(present: Iterable[str], columns: Iterable[str]) -> pd.DataFrame:
    present = set(present)
    return pd.DataFrame([[int(c in present) for c in columns]], columns=list(columns))


def ask_patient(columns: Iterable[str], input_fn: Callable[[str], str] = input,
                print_fn: Callable[[str], None] = print) -> list[str]:
    """Ask about each symptom, re-asking on invalid input. Returns the symptoms answered 'yes'."""
    present = []
    for col in columns:
        while True:
            try:
                answer = parse_yes_no(input_fn(f"Do you have {col.replace('_', ' ')}? [y/n]: "))
                break
            except ValueError as err:
                print_fn(f"  {err}")
        if answer:
            present.append(col)
    return present


# ------------------------------------------------------------------------------ main
def print_quality(q: dict) -> None:
    print(f"Dataset: {q['n_rows']} rows, {q['n_symptoms']} symptoms, {q['n_diseases']} diseases "
          f"({q['rows_per_disease_min']}-{q['rows_per_disease_max']} rows per disease)")
    print(f"Exact duplicate rows: {q['exact_duplicate_rows']} | "
          f"contradictory symptom patterns: {q['symptom_profiles_with_conflicting_labels']}")
    for w in q["warnings"]:
        print(f"  ! {w}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=None, help="CSV of 0/1 symptom columns + a label column")
    ap.add_argument("--target-column", default="disease")
    ap.add_argument("--symptoms", default=None, help="comma-separated symptoms present (skips the questionnaire)")
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--report", action="store_true", help="print data-quality + evaluation and exit")
    ap.add_argument("--outdir", type=Path, default=Path(__file__).parent / "results")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args(argv)
    if args.top_k < 1:
        ap.error("--top-k must be at least 1")

    try:
        X, y = load_dataset(args.data, args.target_column)
    except (ValueError, FileNotFoundError, pd.errors.ParserError) as err:
        print(f"Error loading dataset: {err}", file=sys.stderr)
        return 2
    quality = data_quality_report(X, y)
    print("--- ailment discoverer 3.0 ---")
    if args.report:
        print_quality(quality)
    else:
        print(f"Trained on {quality['n_rows']} rows. Run with --report for data-quality warnings and honest accuracy.")

    if args.report:
        def show(title: str, result: dict) -> None:
            print(f"\n{title} ({result['method']}, n={result['n']}):")
            print(f"  top-1 accuracy {result['top1_accuracy']:.1%}  (95% CI {result['top1_ci95'][0]:.0%}-{result['top1_ci95'][1]:.0%})")
            print(f"  top-3 accuracy {result['top3_accuracy']:.1%}  (95% CI {result['top3_ci95'][0]:.0%}-{result['top3_ci95'][1]:.0%})")
            print(f"  always guessing the most common disease: {result['majority_class_baseline']:.1%}")

        result = evaluate(X, y, args.seed)
        show("Evaluation on all rows", result)
        payload = {"quality": quality, "evaluation": result}
        if quality["exact_duplicate_rows"]:
            # duplicates put an identical twin of every held-out row into the training set
            Xd, yd = deduplicate(X, y)
            result_dedup = evaluate(Xd, yd, args.seed)
            show("Evaluation after removing exact duplicates (stricter: no memorisable twins)", result_dedup)
            payload["evaluation_deduplicated"] = result_dedup
        args.outdir.mkdir(parents=True, exist_ok=True)
        groups = {"All rows": result}
        if "evaluation_deduplicated" in payload:
            groups["Duplicates removed"] = payload["evaluation_deduplicated"]
        plot_evaluation(groups, args.outdir / "evaluation_summary.png")
        (args.outdir / "evaluation.json").write_text(json.dumps(payload, indent=2))
        print(f"\nSaved {args.outdir / 'evaluation.json'}")
        return 0

    model = build_model(args.seed).fit(X, y)
    try:
        if args.symptoms is not None:
            present = parse_symptom_list(args.symptoms, X.columns)
        else:
            print("\nAnswer y or n for each symptom.\n")
            present = ask_patient(X.columns)
    except ValueError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 130

    if not present:
        print("\nNo symptoms entered - nothing to rank.")
        return 0
    ranked = rank_diagnoses(model, vector_from_symptoms(present, X.columns), args.top_k)
    print("\n--- highest-ranked labels (model score; NOT a clinical probability) ---")
    for disease, score in ranked:
        print(f"  {disease}: {score:.0%}")
    print(f"\n{DISCLAIMER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
