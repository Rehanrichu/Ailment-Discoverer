"""Run with:  python -m unittest -v   (from this folder)"""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

import ailment_discoverer as ad


class TestData(unittest.TestCase):
    def setUp(self):
        self.X, self.y = ad.load_dataset()

    def test_default_dataset_shape(self):
        self.assertEqual(self.X.shape, (15, 7))
        self.assertEqual(len(self.y), 15)
        self.assertIn("high_fever", self.X.columns)

    def test_custom_csv_with_other_target_and_stray_column(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "t.csv"
            pd.DataFrame({"a": [0, 1, 1], "b": [1, 0, 1], "prognosis": ["x", "y", "y"],
                          "Unnamed: 3": [None, None, None]}).to_csv(path, index=False)
            X, y = ad.load_dataset(path, "prognosis")
            self.assertEqual(list(X.columns), ["a", "b"])
            self.assertEqual(list(y), ["x", "y", "y"])

    def test_rejects_non_binary_symptom_columns(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "t.csv"
            pd.DataFrame({"a": [0, 2, 1], "disease": ["x", "y", "y"]}).to_csv(path, index=False)
            with self.assertRaises(ValueError):
                ad.load_dataset(path)

    def test_missing_target_column(self):
        with self.assertRaises(ValueError):
            ad.load_dataset(target_column="nope")

    def test_target_and_feature_headers_with_spaces_are_normalised(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "headers.csv"
            pd.DataFrame({
                " Skin Rash ": [0, 1, 0],
                " High Fever ": [1, 0, 1],
                " disease ": ["x", "y", "x"],
            }).to_csv(path, index=False)
            X, y = ad.load_dataset(path, target_column=" disease ")
            self.assertEqual(list(X.columns), ["skin_rash", "high_fever"])
            self.assertEqual(list(y), ["x", "y", "x"])

    def test_column_names_are_normalised(self):
        self.assertEqual(ad.normalize_name(" dischromic _patches"), "dischromic_patches")
        self.assertEqual(ad.normalize_name("Skin Rash"), "skin_rash")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "t.csv"
            pd.DataFrame({"foul_smell_of urine": [0, 1, 1], "spotting_ urination": [1, 0, 1],
                          "prognosis": ["x", "y", "y"]}).to_csv(path, index=False)
            X, _ = ad.load_dataset(path, "prognosis")
            self.assertEqual(list(X.columns), ["foul_smell_of_urine", "spotting_urination"])

    def test_column_name_collision_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "t.csv"
            pd.DataFrame({"skin rash": [0, 1], "skin_rash": [1, 0], "disease": ["x", "y"]}).to_csv(path, index=False)
            with self.assertRaises(ValueError):
                ad.load_dataset(path)

    def test_rejects_missing_symptom_values(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "missing_feature.csv"
            pd.DataFrame({"headache": [0, None], "disease": ["x", "y"]}).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "missing values"):
                ad.load_dataset(path)

    def test_rejects_missing_and_blank_target_labels(self):
        for labels in (["x", None], ["x", "  "]):
            with self.subTest(labels=labels), tempfile.TemporaryDirectory() as d:
                path = Path(d) / "missing_target.csv"
                pd.DataFrame({"headache": [0, 1], "disease": labels}).to_csv(path, index=False)
                with self.assertRaisesRegex(ValueError, "missing or blank labels"):
                    ad.load_dataset(path)

    def test_rejects_non_numeric_symptom_values(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "text_feature.csv"
            pd.DataFrame({"headache": [0, "unknown"], "disease": ["x", "y"]}).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "non-numeric"):
                ad.load_dataset(path)

    def test_deduplicate_removes_only_exact_twins(self):
        Xd, yd = ad.deduplicate(self.X, self.y)
        self.assertEqual(len(Xd), 11)          # 15 rows, 4 exact duplicates
        self.assertEqual(len(Xd), len(yd))
        self.assertEqual(int((yd == "Typhoid").sum()), 1)

    def test_quality_report_finds_known_problems(self):
        q = ad.data_quality_report(self.X, self.y)
        self.assertEqual(q["exact_duplicate_rows"], 4)
        self.assertEqual(q["symptom_profiles_with_conflicting_labels"], 1)  # Chikungunya vs Malaria
        self.assertEqual(q["diseases_with_a_single_row"], ["Amoebiasis", "Chikungunya", "Malaria"])
        self.assertTrue(q["warnings"])


class TestInput(unittest.TestCase):
    def test_parse_yes_no(self):
        for t in ["y", "YES", " 1 ", "true"]:
            self.assertEqual(ad.parse_yes_no(t), 1)
        for t in ["n", "No", "0", "false"]:
            self.assertEqual(ad.parse_yes_no(t), 0)
        with self.assertRaises(ValueError):
            ad.parse_yes_no("maybe")

    def test_parse_symptom_list_normalises(self):
        cols = ["high_fever", "cough", "skin_rash"]
        self.assertEqual(ad.parse_symptom_list("High fever, COUGH", cols), ["high_fever", "cough"])
        self.assertEqual(ad.parse_symptom_list(" high   fever, high_fever ", cols), ["high_fever"])

    def test_parse_symptom_list_suggests_on_typo(self):
        with self.assertRaises(ValueError) as ctx:
            ad.parse_symptom_list("high_feve", ["high_fever", "cough"])
        self.assertIn("high_fever", str(ctx.exception))

    def test_ask_patient_reasks_after_invalid_answer(self):
        answers = iter(["maybe", "y", "n"])  # invalid, then yes for symptom 1, no for symptom 2
        messages = []
        present = ad.ask_patient(["high_fever", "cough"], input_fn=lambda _: next(answers),
                                 print_fn=messages.append)
        self.assertEqual(present, ["high_fever"])
        self.assertEqual(len(messages), 1)  # exactly one complaint about the invalid answer


class TestModel(unittest.TestCase):
    def setUp(self):
        self.X, self.y = ad.load_dataset()
        self.model = ad.build_model().fit(self.X, self.y)

    def test_ranking_is_sorted_and_bounded(self):
        row = ad.vector_from_symptoms(["high_fever", "headache"], self.X.columns)
        ranked = ad.rank_diagnoses(self.model, row, top_k=3)
        scores = [s for _, s in ranked]
        self.assertLessEqual(len(ranked), 3)
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertLessEqual(sum(scores), 1.0 + 1e-9)

    def test_training_pattern_is_recovered(self):
        # fever + stomach pain + headache is the (duplicated) Typhoid pattern in the data
        row = ad.vector_from_symptoms(["high_fever", "stomach_pain", "headache"], self.X.columns)
        self.assertEqual(ad.rank_diagnoses(self.model, row, 1)[0][0], "Typhoid")

    def test_evaluate_returns_consistent_numbers(self):
        r = ad.evaluate(self.X, self.y)
        self.assertEqual(r["method"], "leave-one-out")
        self.assertTrue(0 <= r["top1_accuracy"] <= r["top3_accuracy"] <= 1)
        lo, hi = r["top1_ci95"]
        self.assertTrue(lo <= r["top1_accuracy"] <= hi)

    def test_ranking_rejects_invalid_top_k(self):
        row = ad.vector_from_symptoms(["high_fever"], self.X.columns)
        with self.assertRaisesRegex(ValueError, "at least 1"):
            ad.rank_diagnoses(self.model, row, top_k=0)

    def test_wilson_interval_known_value(self):
        lo, hi = ad.wilson_interval(3, 3)  # 3/3 correct still leaves wide uncertainty
        self.assertAlmostEqual(lo, 0.439, places=2)
        self.assertEqual(hi, 1.0)

    def test_wilson_interval_rejects_invalid_counts(self):
        with self.assertRaises(ValueError):
            ad.wilson_interval(0, 0)
        with self.assertRaises(ValueError):
            ad.wilson_interval(4, 3)


if __name__ == "__main__":
    unittest.main()
