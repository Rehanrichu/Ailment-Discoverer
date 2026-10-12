"""Verify report generation and CLI behavior. Run unit tests separately."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
from pathlib import Path

import ailment_discoverer as ad

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def call_main(*args: str) -> tuple[int, str, str]:
    """Call the CLI entry point and capture its output for assertions."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = ad.main(list(args))
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 1
    return code, stdout.getvalue(), stderr.getvalue()


def main() -> int:
    print("[1/3] Checking report generation and expected dataset findings...", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "results"
        code, report_stdout, report_stderr = call_main("--report", "--outdir", str(output))
        print(report_stdout, end="")
        print(report_stderr, end="")
        require(code == 0, "Report command failed.")
        saved = output / "evaluation.json"
        require(saved.exists(), "Evaluation JSON was not created.")
        payload = json.loads(saved.read_text(encoding="utf-8"))
        quality = payload["quality"]
        metrics = payload["evaluation"]
        require(quality["n_rows"] == 15, "Unexpected number of rows in supplied dataset.")
        require(quality["exact_duplicate_rows"] == 4, "Unexpected duplicate-row count.")
        require(quality["symptom_profiles_with_conflicting_labels"] == 1,
                "Unexpected conflicting-profile count.")
        require(metrics["top1_accuracy"] <= metrics["top3_accuracy"],
                "Top-1 accuracy should not exceed top-3 accuracy.")

    print("[2/3] Checking valid symptoms and typo handling...", flush=True)
    code, output, error = call_main("--symptoms", "high fever, headache, skin rash")
    require(code == 0 and "not a clinical probability" in output.lower(),
            "Valid symptom-list example failed or omitted the score caveat.")
    code, output, error = call_main("--symptoms", "high_feve")
    require(code == 2 and "did you mean" in error.lower(),
            "Typo validation failed.")

    print("[3/3] Checking CLI argument validation...", flush=True)
    code, output, error = call_main("--top-k", "0")
    require(code == 2 and "top-k must be at least 1" in error.lower(),
            "Invalid top-k argument was not rejected.")

    print("PASS: report generation, input validation, and CLI checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
