from dataclasses import FrozenInstanceError

import pytest

from patas_backend.models.compatibility import (
    CompatibilityResult,
    InvalidCompatibilityResult,
)


@pytest.mark.parametrize(
    ("raw", "score"),
    [
        (-12.0, 0),
        (0.0, 0),
        (37.4, 37),
        # Half rounds up, so a score never depends on whether its integer part is odd.
        (37.5, 38),
        (62.5, 63),
        (100.0, 100),
        (140.0, 100),
    ],
)
def test_scored_rounds_half_up_and_clamps_to_the_score_range(
    raw: float, score: int
) -> None:
    assert CompatibilityResult.scored(raw, []).score == score


def test_scored_keeps_the_reasons_in_order_and_is_compatible() -> None:
    result = CompatibilityResult.scored(80, ["first", "second"])

    assert result.reasons == ("first", "second")
    assert result.is_compatible


def test_excluded_scores_zero_and_says_why() -> None:
    result = CompatibilityResult.excluded("Not safe with children")

    assert result.score == 0
    assert result.reasons == ("Not safe with children",)
    assert not result.is_compatible


@pytest.mark.parametrize("score", [-1, 101])
def test_a_score_outside_the_range_is_rejected(score: int) -> None:
    with pytest.raises(InvalidCompatibilityResult):
        CompatibilityResult(score=score, reasons=())


def test_an_incompatible_result_with_a_score_is_rejected() -> None:
    with pytest.raises(InvalidCompatibilityResult):
        CompatibilityResult(score=40, reasons=("why",), is_compatible=False)


def test_an_incompatible_result_without_a_reason_is_rejected() -> None:
    with pytest.raises(InvalidCompatibilityResult):
        CompatibilityResult(score=0, reasons=(), is_compatible=False)


def test_a_result_cannot_be_changed_after_it_is_built() -> None:
    result = CompatibilityResult.scored(50, [])

    with pytest.raises(FrozenInstanceError):
        result.score = 99  # type: ignore[misc]
