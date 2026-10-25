import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer

CARLA = {"sub": "5d0c7a52-3b1e-4c8f-9a6d-2e4f8b1c7d90",
         "email": "carla@example.com", "name": "Carla"}  # fmt: skip
BRUNO = {"sub": "8e1f3b6a-2c4d-4e5f-8a7b-1c2d3e4f5a6b",
         "email": "bruno@example.com", "name": "Bruno"}  # fmt: skip

# Carla's answers from AT-07.
CARLAS_ANSWERS = {
    "housing": "apartment",
    "activity": "low",
    "time_away": "few_hours",
    "experience": "some",
    "has_children": False,
    "has_dogs": False,
    "has_cats": True,
}
BRUNOS_ANSWERS = {
    "housing": "house_with_yard",
    "activity": "high",
    "time_away": "half_day",
    "experience": "experienced",
    "has_children": True,
    "has_dogs": True,
    "has_cats": False,
}
PROFILE = "/me/matchmaker-profile"


def _as(issuer: TokenIssuer, person: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {issuer.token(**person)}"}


async def _stored_profiles(engine: AsyncEngine) -> int:
    async with engine.connect() as conn:
        return await conn.scalar(text("SELECT count(*) FROM patas.matchmaker_profiles"))


async def test_a_user_without_a_profile_gets_404(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    response = await client.get(PROFILE, headers=_as(issuer, CARLA))

    # The detail tells our 404 from the router's "Not Found" for an unknown route.
    assert response.status_code == 404
    assert response.json() == {"detail": "No Matchmaker profile yet"}


async def test_at_07_saved_answers_show_up_on_the_next_visit(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    saved = await client.put(PROFILE, json=CARLAS_ANSWERS, headers=_as(issuer, CARLA))

    assert saved.status_code == 200
    assert saved.json() == CARLAS_ANSWERS
    visit = await client.get(PROFILE, headers=_as(issuer, CARLA))
    assert visit.status_code == 200
    assert visit.json() == CARLAS_ANSWERS


async def test_at_07_changing_an_answer_updates_the_profile_and_keeps_only_one(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await client.put(PROFILE, json=CARLAS_ANSWERS, headers=_as(issuer, CARLA))
    changed = {**CARLAS_ANSWERS, "has_dogs": True}

    response = await client.put(PROFILE, json=changed, headers=_as(issuer, CARLA))

    assert response.status_code == 200
    visit = await client.get(PROFILE, headers=_as(issuer, CARLA))
    assert visit.json() == changed
    assert await _stored_profiles(engine) == 1


async def test_at_07_an_invalid_answer_is_rejected_and_the_profile_is_unchanged(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    await client.put(PROFILE, json=CARLAS_ANSWERS, headers=_as(issuer, CARLA))

    response = await client.put(
        PROFILE,
        json={**CARLAS_ANSWERS, "housing": "castle"},
        headers=_as(issuer, CARLA),
    )

    assert response.status_code == 422
    visit = await client.get(PROFILE, headers=_as(issuer, CARLA))
    assert visit.json() == CARLAS_ANSWERS


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(
            {k: v for k, v in CARLAS_ANSWERS.items() if k != "has_cats"},
            id="missing-answer",
        ),
        pytest.param({**CARLAS_ANSWERS, "housing": None}, id="null-answer"),
        pytest.param({**CARLAS_ANSWERS, "activity": "extreme"}, id="unknown-activity"),
        pytest.param({**CARLAS_ANSWERS, "has_cats": "yes"}, id="text-for-yes-or-no"),
    ],
)
async def test_an_incomplete_or_malformed_profile_is_rejected_and_nothing_is_stored(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    body: dict[str, object],
) -> None:
    response = await client.put(PROFILE, json=body, headers=_as(issuer, CARLA))

    assert response.status_code == 422
    assert await _stored_profiles(engine) == 0


async def test_at_08_each_user_sees_only_their_own_profile(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    await client.put(PROFILE, json=CARLAS_ANSWERS, headers=_as(issuer, CARLA))
    await client.put(PROFILE, json=BRUNOS_ANSWERS, headers=_as(issuer, BRUNO))

    brunos = await client.get(PROFILE, headers=_as(issuer, BRUNO))
    carlas = await client.get(PROFILE, headers=_as(issuer, CARLA))

    assert brunos.json() == BRUNOS_ANSWERS
    assert carlas.json() == CARLAS_ANSWERS


async def test_at_08_a_visitor_cannot_save_and_nothing_is_stored(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    response = await client.put(PROFILE, json=CARLAS_ANSWERS)

    assert response.status_code == 401
    assert await _stored_profiles(engine) == 0


async def test_a_visitor_cannot_read_a_profile(client: httpx.AsyncClient) -> None:
    assert (await client.get(PROFILE)).status_code == 401
