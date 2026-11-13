"""Metrics report: one row per merge, backend and frontend side by side.

Usage (see the `report` job in .github/workflows/ci.yml):
    python scripts/quality/report.py --metrics metrics.json --html index.html \\
        --branch staging --commit fae7e62 --date 2026-11-13T16:40:00Z --title "..." \\
        --repo-url https://github.com/org/repo \\
        --backend-junit junit-unit.xml junit-integration.xml junit-acceptance.xml \\
        --backend-coverage coverage.json --backend-diff diff-backend.json \\
        --frontend-tests test-results.json --frontend-coverage coverage-summary.json \\
        --frontend-diff diff-frontend.json --mutation mutmut-cicd-stats.json

A number that could not be read is left empty (null) and shown as "n/d". It is never
turned into 0, which would read as a measurement.
"""

import argparse
import html
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import gate
import mutation


def backend_tests(junit_paths: list[Path]) -> int:
    """Tests run, summed over the JUnit files of the unit, integration and acceptance steps."""
    return sum(
        int(suite.get("tests", 0))
        for path in junit_paths
        for suite in ET.parse(path).iter("testsuite")
    )


def frontend_tests(results: dict) -> int:
    return results["numTotalTests"]


def branch_pct(branches: tuple[int, int]) -> float:
    return round(gate.percent(*branches), 1)


def diff_pct(report: dict) -> float | None:
    """Coverage of the lines the merge changed, or None when it changed none that count."""
    if report["total_num_lines"] == 0:
        return None
    return round(float(report["total_percent_covered"]), 1)


def mutation_pct(stats: dict) -> float:
    killed, scored = mutation.score(stats)
    return round(100.0 * killed / scored, 1)


def attempt(read, path: Path | list[Path] | None):
    """The value read from a report, or None if it is missing or not what was expected."""
    if path is None:
        return None
    try:
        return read(path)
    except (OSError, ValueError, KeyError, ZeroDivisionError, ET.ParseError):
        return None


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def build_row(
    *,
    date: str,
    branch: str,
    commit: str,
    title: str,
    backend: dict,
    frontend: dict,
    mutation_score: float | None,
) -> dict:
    return {
        "date": date,
        "branch": branch,
        "commit": commit,
        "title": title,
        "backend": backend,
        "frontend": frontend,
        "mutation_pct": mutation_score,
    }


def append(history: list[dict], row: dict) -> list[dict]:
    """Adds the row; a rerun for the same commit and branch replaces its row."""
    key = (row["commit"], row["branch"])
    return [old for old in history if (old["commit"], old["branch"]) != key] + [row]


def _cell(value, suffix: str = "") -> str:
    return "n/d" if value is None else f"{value}{suffix}"


def _side(side: dict) -> str:
    return (
        f"<td>{_cell(side['tests'])}</td>"
        f"<td>{_cell(side['branch_pct'], '%')}</td>"
        f"<td>{_cell(side['diff_pct'], '%')}</td>"
    )


STYLE = """
:root { --bg:#fff; --fg:#1d2327; --muted:#5c6770; --line:#d8dde1; --card:#f4f6f7; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#14181b; --fg:#e8ecee; --muted:#9aa5ad; --line:#2b3237; --card:#1c2226; }
}
body { margin:0; padding:24px 16px; background:var(--bg); color:var(--fg);
       font:15px/1.5 system-ui, sans-serif; }
main { max-width:1100px; margin:0 auto; }
h1 { font-size:1.4rem; margin:0 0 4px; } p.sub { color:var(--muted); margin:0 0 20px; }
.cards { display:grid; gap:12px; margin-bottom:24px;
         grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); }
.card { background:var(--card); border:1px solid var(--line); border-radius:8px;
        padding:12px 14px; }
.card h2 { font-size:.8rem; color:var(--muted); margin:0 0 4px; font-weight:600;
           text-transform:uppercase; }
.card .n { font-size:1.6rem; font-weight:650; }
.card .d { color:var(--muted); font-size:.85rem; }
.scroll { overflow-x:auto; }
table { border-collapse:collapse; width:100%; min-width:860px; }
th, td { padding:6px 10px; border-bottom:1px solid var(--line); text-align:right;
         white-space:nowrap; }
th { color:var(--muted); font-weight:600; font-size:.8rem; }
td.l, th.l { text-align:left; }
td.l.t { white-space:normal; min-width:200px; } a { color:inherit; }
"""


def render(history: list[dict], repo_url: str = "") -> str:
    rows = sorted(history, key=lambda r: r["date"], reverse=True)
    latest = rows[0] if rows else None

    def card(title: str, value, detail: str) -> str:
        return (
            f'<div class="card"><h2>{html.escape(title)}</h2>'
            f'<div class="n">{html.escape(_cell(value))}</div>'
            f'<div class="d">{html.escape(detail)}</div></div>'
        )

    cards = ""
    if latest:
        b, f = latest["backend"], latest["frontend"]
        cards = (
            card(
                "Backend tests",
                b["tests"],
                f"branch coverage {_cell(b['branch_pct'], '%')}",
            )
            + card(
                "Frontend tests",
                f["tests"],
                f"branch coverage {_cell(f['branch_pct'], '%')}",
            )
            + card(
                "Mutation score",
                None if latest["mutation_pct"] is None else f"{latest['mutation_pct']}%",
                "domain, unit tests",
            )
        )

    body = ""
    for row in rows:
        commit = html.escape(row["commit"])
        link = (
            f'<a href="{html.escape(repo_url)}/commit/{commit}">{commit}</a>'
            if repo_url
            else commit
        )
        mutation_cell = _cell(row["mutation_pct"], "%")
        body += (
            f'<tr><td class="l">{html.escape(row["date"][:16].replace("T", " "))}</td>'
            f'<td class="l">{html.escape(row["branch"])}</td><td class="l">{link}</td>'
            f'<td class="l t">{html.escape(row["title"])}</td>'
            f"{_side(row['backend'])}{_side(row['frontend'])}<td>{mutation_cell}</td></tr>"
        )
    if not body:
        body = '<tr><td class="l" colspan="12">No merge measured yet.</td></tr>'

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Patas metrics</title><style>{STYLE}</style></head>
<body><main>
<h1>Patas metrics</h1>
<p class="sub">One row per merge. Levels and scope: docs/process/TESTING.md.
n/d: not measured in that run.</p>
<div class="cards">{cards}</div>
<div class="scroll"><table>
<thead><tr><th class="l" rowspan="2">Date (UTC)</th><th class="l" rowspan="2">Branch</th>
<th class="l" rowspan="2">Commit</th><th class="l" rowspan="2">Change</th>
<th colspan="3">Backend</th><th colspan="3">Frontend</th><th rowspan="2">Mutation</th></tr>
<tr><th>Tests</th><th>Branch</th><th>Changed lines</th>
<th>Tests</th><th>Branch</th><th>Changed lines</th></tr></thead>
<tbody>{body}</tbody></table></div>
</main></body></html>
"""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--repo-url", default="")
    parser.add_argument("--backend-junit", type=Path, nargs="*", default=[])
    parser.add_argument("--backend-coverage", type=Path)
    parser.add_argument("--backend-diff", type=Path)
    parser.add_argument("--frontend-tests", type=Path)
    parser.add_argument("--frontend-coverage", type=Path)
    parser.add_argument("--frontend-diff", type=Path)
    parser.add_argument("--mutation", type=Path)
    args = parser.parse_args(argv[1:])

    def side(tests, coverage, read_branches, diff) -> dict:
        return {
            "tests": tests,
            "branch_pct": attempt(lambda p: branch_pct(read_branches(load(p))), coverage),
            "diff_pct": attempt(lambda p: diff_pct(load(p)), diff),
        }

    row = build_row(
        date=args.date,
        branch=args.branch,
        commit=args.commit,
        title=args.title,
        backend=side(
            attempt(lambda paths: backend_tests(paths), args.backend_junit or None),
            args.backend_coverage,
            gate.backend_branches,
            args.backend_diff,
        ),
        frontend=side(
            attempt(lambda p: frontend_tests(load(p)), args.frontend_tests),
            args.frontend_coverage,
            gate.frontend_branches,
            args.frontend_diff,
        ),
        mutation_score=attempt(lambda p: mutation_pct(load(p)), args.mutation),
    )
    try:
        history = json.loads(args.metrics.read_text())
    except FileNotFoundError:
        history = []
    history = append(history, row)
    args.metrics.write_text(json.dumps(history, indent=2) + "\n")
    args.html.write_text(render(history, args.repo_url))
    print(f"report: {len(history)} rows, last {row['branch']}@{row['commit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
