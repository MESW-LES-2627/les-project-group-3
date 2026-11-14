"""Branch-coverage gate (docs/process/TESTING.md).

Usage:
    python scripts/quality/gate.py backend  patas-backend/coverage.json
    python scripts/quality/gate.py frontend patas-frontend/coverage/coverage-summary.json

Each side is checked against the floor in quality.json. A missing or unreadable report
fails the gate: a report that was not produced must never read as a pass.
"""

import json
import sys
from pathlib import Path

LEVELS_FILE = Path(__file__).resolve().parents[2] / "quality.json"


def percent(covered: int, total: int) -> float:
    """No branches means nothing can be uncovered."""
    return 100.0 if total == 0 else 100.0 * covered / total


def backend_branches(report: dict) -> tuple[int, int]:
    """(covered, total) from coverage.py's JSON report, which needs branch = true."""
    totals = report["totals"]
    return totals["covered_branches"], totals["num_branches"]


def frontend_branches(report: dict) -> tuple[int, int]:
    """(covered, total) from Vitest's json-summary report."""
    branches = report["total"]["branches"]
    return branches["covered"], branches["total"]


READERS = {"backend": backend_branches, "frontend": frontend_branches}


def below_floor(side: str, branches: tuple[int, int], floor: float) -> str | None:
    covered, total = branches
    achieved = percent(covered, total)
    if achieved < floor:
        return (
            f"{side}: branch coverage {achieved:.1f}% ({covered}/{total}) "
            f"is below the {floor:g}% floor"
        )
    return None


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in READERS:
        print(__doc__)
        return 2
    side, report_path = argv[1], Path(argv[2])
    try:
        floor = json.loads(LEVELS_FILE.read_text())["branch_coverage_min"]
        branches = READERS[side](json.loads(report_path.read_text()))
    except (OSError, ValueError, KeyError) as error:
        print(f"{side}: cannot read the coverage report ({error!r})")
        return 1

    covered, total = branches
    print(
        f"{side}: branch coverage {percent(covered, total):.1f}% "
        f"({covered}/{total}), floor {floor:g}%"
    )
    problem = below_floor(side, branches, floor)
    if problem:
        print(problem)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
