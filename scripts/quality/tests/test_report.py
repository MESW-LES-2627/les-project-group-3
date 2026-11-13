import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import report  # noqa: E402

JUNIT = '<?xml version="1.0"?><testsuites><testsuite name="pytest" tests="{n}"/></testsuites>'


def side(tests=10, branch=90.0, diff=100.0) -> dict:
    return {"tests": tests, "branch_pct": branch, "diff_pct": diff}


def row(commit="abc1234", branch="staging", date="2026-11-13T10:00:00Z", **side_args):
    return report.build_row(
        date=date,
        branch=branch,
        commit=commit,
        title="Merge pull request #1",
        backend=side(**side_args),
        frontend=side(),
        mutation_score=76.3,
    )


class ReadingTheReportsTest(unittest.TestCase):
    def test_backend_tests_are_summed_over_the_three_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for name, count in [("u", 382), ("i", 250), ("a", 26)]:
                path = Path(tmp) / f"{name}.xml"
                path.write_text(JUNIT.format(n=count))
                paths.append(path)

            self.assertEqual(report.backend_tests(paths), 658)

    def test_frontend_tests_come_from_the_vitest_summary(self):
        self.assertEqual(report.frontend_tests({"numTotalTests": 128}), 128)

    def test_diff_coverage_is_rounded_to_one_decimal(self):
        self.assertEqual(
            report.diff_pct({"total_num_lines": 7, "total_percent_covered": 85.714}),
            85.7,
        )

    def test_a_merge_that_changed_no_measured_line_has_no_diff_coverage(self):
        self.assertIsNone(report.diff_pct({"total_num_lines": 0, "total_percent_covered": 100}))

    def test_mutation_score_is_rounded_to_one_decimal(self):
        stats = {
            "killed": 692,
            "survived": 215,
            "no_tests": 0,
            "skipped": 0,
            "total": 907,
        }
        self.assertEqual(report.mutation_pct(stats), 76.3)

    def test_a_missing_or_malformed_report_is_none_never_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps({"unexpected": 1}))

            self.assertIsNone(report.attempt(report.load, Path(tmp) / "missing.json"))
            self.assertIsNone(report.attempt(lambda p: report.load(p)["total"], bad))
            self.assertIsNone(report.attempt(report.load, None))

    def test_no_mutants_tried_is_none_not_zero(self):
        empty = {"killed": 0, "survived": 0, "no_tests": 0, "skipped": 0, "total": 0}

        self.assertIsNone(report.attempt(lambda _: report.mutation_pct(empty), Path("x")))


class AppendTest(unittest.TestCase):
    def test_adds_a_row(self):
        self.assertEqual(len(report.append([row("a")], row("b"))), 2)

    def test_a_rerun_of_the_same_commit_replaces_its_row(self):
        history = report.append([row("a", tests=1)], row("a", tests=2))

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["backend"]["tests"], 2)

    def test_the_same_commit_on_another_branch_is_another_row(self):
        history = report.append([row("a", branch="staging")], row("a", branch="main"))

        self.assertEqual(len(history), 2)


class RenderTest(unittest.TestCase):
    def test_lists_the_newest_merge_first(self):
        page = report.render(
            [
                row("old1234", date="2026-11-01T10:00:00Z"),
                row("new5678", date="2026-11-13T10:00:00Z"),
            ]
        )

        self.assertLess(page.index("new5678"), page.index("old1234"))

    def test_shows_what_was_not_measured_as_n_d(self):
        page = report.render([row(diff=None)])

        self.assertIn("n/d", page)

    def test_escapes_what_comes_from_a_commit_message(self):
        hostile = report.build_row(
            date="2026-11-13T10:00:00Z",
            branch="staging",
            commit="abc1234",
            title="<script>alert(1)</script>",
            backend=side(),
            frontend=side(),
            mutation_score=None,
        )

        page = report.render([hostile])

        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_an_empty_history_says_so(self):
        self.assertIn("No merge measured yet", report.render([]))

    def test_links_the_commit_when_the_repository_is_known(self):
        page = report.render([row("abc1234")], "https://github.com/org/repo")

        self.assertIn('href="https://github.com/org/repo/commit/abc1234"', page)


class MainTest(unittest.TestCase):
    def test_writes_the_history_and_the_page_and_keeps_earlier_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            metrics, page = Path(tmp) / "metrics.json", Path(tmp) / "index.html"
            metrics.write_text(json.dumps([row("earlier")]))

            code = report.main(
                [
                    "report",
                    "--metrics",
                    str(metrics),
                    "--html",
                    str(page),
                    "--branch",
                    "staging",
                    "--commit",
                    "abc1234",
                    "--date",
                    "2026-11-13T10:00:00Z",
                    "--title",
                    "Merge pull request #2",
                ]
            )

            self.assertEqual(code, 0)
            history = json.loads(metrics.read_text())
            self.assertEqual([r["commit"] for r in history], ["earlier", "abc1234"])
            # Nothing was passed to read, so nothing is claimed: no zeros.
            self.assertIsNone(history[1]["backend"]["tests"])
            self.assertIsNone(history[1]["mutation_pct"])
            self.assertIn("abc1234", page.read_text())


if __name__ == "__main__":
    unittest.main()
