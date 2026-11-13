import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gate  # noqa: E402


def write(directory: str, name: str, content: dict) -> str:
    path = Path(directory) / name
    path.write_text(json.dumps(content))
    return str(path)


def backend_report(covered: int, total: int) -> dict:
    return {"totals": {"covered_branches": covered, "num_branches": total}}


def frontend_report(covered: int, total: int) -> dict:
    return {"total": {"branches": {"covered": covered, "total": total}}}


class PercentTest(unittest.TestCase):
    def test_a_share_of_the_branches(self):
        self.assertEqual(gate.percent(86, 100), 86.0)

    def test_no_branches_leaves_nothing_uncovered(self):
        self.assertEqual(gate.percent(0, 0), 100.0)


class ReadersTest(unittest.TestCase):
    def test_reads_coverage_py_branches(self):
        self.assertEqual(gate.backend_branches(backend_report(150, 172)), (150, 172))

    def test_reads_vitest_branches(self):
        self.assertEqual(gate.frontend_branches(frontend_report(190, 195)), (190, 195))


class BelowFloorTest(unittest.TestCase):
    def test_exactly_the_floor_passes(self):
        self.assertIsNone(gate.below_floor("backend", (85, 100), 85))

    def test_just_under_the_floor_fails_and_says_where(self):
        message = gate.below_floor("frontend", (84, 100), 85)

        self.assertIn("frontend", message)
        self.assertIn("84.0%", message)
        self.assertIn("85%", message)


class MainTest(unittest.TestCase):
    def test_passes_when_the_side_is_above_the_floor(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = write(tmp, "c.json", backend_report(95, 100))

            self.assertEqual(gate.main(["gate", "backend", report]), 0)

    def test_fails_when_the_side_is_below_the_floor(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = write(tmp, "c.json", frontend_report(50, 100))

            self.assertEqual(gate.main(["gate", "frontend", report]), 1)

    def test_a_missing_report_fails_instead_of_passing(self):
        self.assertEqual(gate.main(["gate", "backend", "does-not-exist.json"]), 1)

    def test_a_report_of_the_wrong_shape_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = write(tmp, "c.json", {"unexpected": True})

            self.assertEqual(gate.main(["gate", "backend", report]), 1)

    def test_an_unknown_side_is_a_usage_error(self):
        self.assertEqual(gate.main(["gate", "mobile", "x.json"]), 2)


if __name__ == "__main__":
    unittest.main()
