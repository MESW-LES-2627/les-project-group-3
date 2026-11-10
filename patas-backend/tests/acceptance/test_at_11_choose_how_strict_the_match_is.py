"""AT-11 (#41): I can choose how strict the match is."""

import httpx
from compatibility_endpoint import BRUNO, CARLA, MILO, _as, _publish, _save_home, _url
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer

from patas_backend.models.compatibility import rules


async def test_at_11_the_strict_match_recalculates_the_score(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    await _save_home(client, issuer, CARLA)

    response = await client.get(_url(animal, "strict"), headers=_as(issuer, CARLA))

    # The same 0.75 base, scaled by 0.75 for the weakest link (0.5): 56.25.
    assert response.status_code == 200
    assert response.json()["mode"] == "strict"
    assert response.json()["score"] == 56
    assert response.json()["is_compatible"] is True


async def test_at_11_a_clear_shortfall_is_not_suitable_in_strict_only(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    # Away most of the day, for an animal that tolerates a few hours alone.
    await _save_home(client, issuer, CARLA, time_away="most_of_day")

    strict = await client.get(_url(animal, "strict"), headers=_as(issuer, CARLA))
    loose = await client.get(_url(animal, "loose"), headers=_as(issuer, CARLA))

    assert strict.json()["is_compatible"] is False
    assert strict.json()["score"] == 0
    assert strict.json()["reasons"] == [
        {"text": rules.TIME_ALONE_WORDING.misfit, "kind": "concern"}
    ]
    assert loose.json()["is_compatible"] is True
    assert rules.TIME_ALONE_WORDING.misfit in [
        reason["text"] for reason in loose.json()["reasons"]
    ]


async def test_at_11_the_mode_defaults_to_loose_and_rejects_unknown_values(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    await _save_home(client, issuer, CARLA)
    headers = _as(issuer, CARLA)

    default = await client.get(_url(animal), headers=headers)
    explicit = await client.get(_url(animal, "loose"), headers=headers)
    unknown = await client.get(_url(animal, "gentle"), headers=headers)

    assert default.json() == explicit.json()
    assert unknown.status_code == 422


async def test_at_11_one_users_mode_does_not_change_what_another_sees(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    await _save_home(client, issuer, CARLA)
    await _save_home(client, issuer, BRUNO)

    carla = await client.get(_url(animal, "strict"), headers=_as(issuer, CARLA))
    bruno = await client.get(_url(animal), headers=_as(issuer, BRUNO))

    assert carla.json()["mode"] == "strict"
    assert bruno.json()["mode"] == "loose"
    assert bruno.json()["score"] == 75
