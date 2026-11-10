import httpx
import pytest
from matchmaker_endpoint import (
    BRUNO,
    BRUNOS_ANSWERS,
    CARLA,
    CARLAS_ANSWERS,
    PROFILE,
    _as,
    _stored_profiles,
)
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer


async def test_a_user_without_a_profile_gets_404(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    response = await client.get(PROFILE, headers=_as(issuer, CARLA))

    # The detail tells our 404 from the router's "Not Found" for an unknown route.
    assert response.status_code == 404
    assert response.json() == {"detail": "No Matchmaker profile yet"}


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


async def test_a_visitor_cannot_read_a_profile(client: httpx.AsyncClient) -> None:
    assert (await client.get(PROFILE)).status_code == 401


async def test_deleting_the_profile_brings_back_the_empty_questions(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await client.put(PROFILE, json=CARLAS_ANSWERS, headers=_as(issuer, CARLA))

    deleted = await client.delete(PROFILE, headers=_as(issuer, CARLA))

    assert deleted.status_code == 204
    assert deleted.content == b""
    visit = await client.get(PROFILE, headers=_as(issuer, CARLA))
    assert visit.status_code == 404
    assert await _stored_profiles(engine) == 0


async def test_a_deleted_profile_can_be_saved_again(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    await client.put(PROFILE, json=CARLAS_ANSWERS, headers=_as(issuer, CARLA))
    deleted = await client.delete(PROFILE, headers=_as(issuer, CARLA))
    # Without this the save below would just overwrite the old profile.
    assert deleted.status_code == 204
    assert (await client.get(PROFILE, headers=_as(issuer, CARLA))).status_code == 404
    again = {**CARLAS_ANSWERS, "housing": "house_with_yard"}

    await client.put(PROFILE, json=again, headers=_as(issuer, CARLA))

    visit = await client.get(PROFILE, headers=_as(issuer, CARLA))
    assert visit.json() == again


async def test_deleting_my_profile_leaves_other_profiles_alone(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    await client.put(PROFILE, json=CARLAS_ANSWERS, headers=_as(issuer, CARLA))
    await client.put(PROFILE, json=BRUNOS_ANSWERS, headers=_as(issuer, BRUNO))

    await client.delete(PROFILE, headers=_as(issuer, BRUNO))

    carlas = await client.get(PROFILE, headers=_as(issuer, CARLA))
    assert carlas.json() == CARLAS_ANSWERS
    brunos = await client.get(PROFILE, headers=_as(issuer, BRUNO))
    assert brunos.status_code == 404


async def test_deleting_when_there_is_no_profile_still_succeeds(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    response = await client.delete(PROFILE, headers=_as(issuer, CARLA))

    assert response.status_code == 204


async def test_a_visitor_cannot_delete_a_profile(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await client.put(PROFILE, json=CARLAS_ANSWERS, headers=_as(issuer, CARLA))

    response = await client.delete(PROFILE)

    assert response.status_code == 401
    assert await _stored_profiles(engine) == 1
