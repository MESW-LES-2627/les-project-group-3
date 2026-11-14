"""Mutation score of the domain (docs/process/TESTING.md).

Usage:
    python scripts/quality/mutation.py mutants/mutmut-cicd-stats.json

Prints the score. It never blocks on the score itself, but it fails when there is no
score to report: no mutants, or a report that cannot be read. A run that did not happen
must not look like a number.
"""

import json
import sys
from pathlib import Path


def score(stats: dict) -> tuple[int, int]:
    """(killed, scored): mutants the tests noticed, out of all that were tried.

    Mutants no test reaches count as not noticed. Skipped ones are left out.
    """
    scored = stats["total"] - stats["skipped"]
    return stats["killed"], scored


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    try:
        killed, scored = score(json.loads(Path(argv[1]).read_text()))
    except (OSError, ValueError, KeyError) as error:
        print(f"mutation: cannot read the report ({error!r})")
        return 1
    if scored <= 0:
        print("mutation: no mutants were tried, so there is no score")
        return 1
    print(f"mutation: {100.0 * killed / scored:.1f}% ({killed}/{scored} mutants noticed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
