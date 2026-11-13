import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mutation  # noqa: E402


def stats(killed: int, survived: int, no_tests: int = 0, skipped: int = 0) -> dict:
    return {
        "killed": killed,
        "survived": survived,
        "no_tests": no_tests,
        "skipped": skipped,
        "total": killed + survived + no_tests + skipped,
    }


def report(directory: str, content: dict) -> str:
    path = Path(directory) / "stats.json"
    path.write_text(json.dumps(content))
    return str(path)


class ScoreTest(unittest.TestCase):
    def test_counts_the_mutants_the_tests_noticed_out_of_all_tried(self):
        self.assertEqual(mutation.score(stats(killed=692, survived=215)), (692, 907))

    def test_a_mutant_no_test_reaches_counts_as_not_noticed(self):
        self.assertEqual(
            mutation.score(stats(killed=50, survived=10, no_tests=40)), (50, 100)
        )

    def test_skipped_mutants_are_left_out(self):
        self.assertEqual(
            mutation.score(stats(killed=8, survived=2, skipped=5)), (8, 10)
        )


class MainTest(unittest.TestCase):
    def test_reports_a_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                mutation.main(["m", report(tmp, stats(killed=8, survived=2))]), 0
            )

    def test_fails_when_no_mutant_was_tried(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = {"killed": 0, "survived": 0, "no_tests": 0, "skipped": 0, "total": 0}
            self.assertEqual(mutation.main(["m", report(tmp, empty)]), 1)

    def test_fails_when_the_report_is_missing_or_malformed(self):
        self.assertEqual(mutation.main(["m", "does-not-exist.json"]), 1)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(mutation.main(["m", report(tmp, {"unexpected": 1})]), 1)


if __name__ == "__main__":
    unittest.main()
