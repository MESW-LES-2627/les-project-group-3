import asyncio
from uuid import UUID

import pytest
from adoption_factory import until_blocked
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from patas_backend.models.user import (
    EmailAlreadyRegistered,
    User,
    UsernameTaken,
    UserRepository,
)

ANA_ID = UUID("0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b")
BOB_ID = UUID("5c6d7e8f-9a0b-4c1d-8e2f-3a4b5c6d7e8f")

Factory = async_sessionmaker[AsyncSession]


def _ana(**overrides: str) -> User:
    return User.provision(
        **{"id": ANA_ID, "name": "Ana", "email": "ana@example.com", **overrides}
    )


async def _ensure(factory: Factory, user: User) -> User:
    async with factory.begin() as session:
        return await UserRepository(session).ensure_exists(user)


async def _rows(engine: AsyncEngine) -> list[tuple[UUID, str, str, bool]]:
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id, name, email, is_platform_admin FROM patas.users")
        )
        return [tuple(row) for row in result]


async def test_creates_the_user_on_first_call(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    returned = await _ensure(session_factory, _ana())

    assert returned == _ana()
    assert await _rows(engine) == [(ANA_ID, "Ana", "ana@example.com", False)]


async def test_second_call_does_not_duplicate(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    await _ensure(session_factory, _ana())
    returned = await _ensure(session_factory, _ana())

    assert returned == _ana()
    assert len(await _rows(engine)) == 1


async def test_existing_user_is_not_overwritten(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    await _ensure(session_factory, _ana())

    returned = await _ensure(session_factory, _ana(name="Ana Maria"))

    assert returned.name == "Ana"
    assert await _rows(engine) == [(ANA_ID, "Ana", "ana@example.com", False)]


async def test_concurrent_first_requests_create_one_row(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    results = await asyncio.gather(
        *(_ensure(session_factory, _ana()) for _ in range(5))
    )

    assert results == [_ana()] * 5
    assert len(await _rows(engine)) == 1


async def test_a_first_request_that_meets_another_for_the_same_user_waits_for_it(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    # Both miss the fast-path SELECT; the second INSERT waits on the first's row,
    # then ON CONFLICT (id) makes it a no-op instead of an error.
    async with session_factory.begin() as session:
        await UserRepository(session).ensure_exists(_ana())
        second = asyncio.create_task(_ensure(session_factory, _ana()))
        await until_blocked(engine, 1)

    assert await second == _ana()
    assert len(await _rows(engine)) == 1


async def test_email_owned_by_another_user_is_rejected(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    await _ensure(session_factory, _ana())

    with pytest.raises(EmailAlreadyRegistered):
        await _ensure(session_factory, _ana(id=BOB_ID, email="ANA@Example.com"))

    assert await _rows(engine) == [(ANA_ID, "Ana", "ana@example.com", False)]


async def test_admin_flag_comes_from_the_database(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO patas.users"
                " (id, name, email, username, is_platform_admin)"
                " VALUES (:id, 'Ana', 'ana@example.com', 'ana', true)"
            ),
            {"id": ANA_ID},
        )

    returned = await _ensure(session_factory, _ana())

    assert returned.is_platform_admin is True


async def test_update_persists_name_change(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    user = await _ensure(session_factory, _ana())
    user.change_name("Ana Silva")

    async with session_factory.begin() as session:
        updated = await UserRepository(session).update(user)

    assert updated.name == "Ana Silva"
    assert await _rows(engine) == [(ANA_ID, "Ana Silva", "ana@example.com", False)]


def _bob(**overrides: str) -> User:
    return User.provision(
        **{"id": BOB_ID, "name": "Bob", "email": "bob@example.com", **overrides}
    )


async def _usernames(engine: AsyncEngine) -> dict[UUID, str]:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, username FROM patas.users"))
        return {row.id: row.username for row in result}


async def test_a_new_user_whose_derived_username_is_taken_gets_the_next_one(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    await _ensure(session_factory, _ana())

    async with session_factory.begin() as session:
        repo = UserRepository(session)
        returned = await repo.ensure_exists(_bob(name="Ana"))
        # The refused first attempt did not abort the caller's transaction.
        assert await repo.is_username_taken("ana2")

    assert returned.username == "ana2"
    assert await _usernames(engine) == {ANA_ID: "ana", BOB_ID: "ana2"}


async def test_a_new_user_is_refused_when_every_candidate_is_taken(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    taken = ["ana", *(f"ana{n}" for n in range(2, 10)), f"ana_{BOB_ID.hex[:8]}"]
    async with engine.begin() as conn:
        for number, username in enumerate(taken):
            await conn.execute(
                text(
                    "INSERT INTO patas.users (id, name, email, username) "
                    "VALUES (gen_random_uuid(), 'Ana', :email, :username)"
                ),
                {"email": f"ana{number}@example.com", "username": username},
            )

    with pytest.raises(UsernameTaken):
        await _ensure(session_factory, _bob(name="Ana"))


async def test_update_persists_a_username_change(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    user = await _ensure(session_factory, _ana())
    user.change_username("Ana.Demo")

    async with session_factory.begin() as session:
        updated = await UserRepository(session).update(user)

    assert updated.username == "Ana.Demo"
    assert await _usernames(engine) == {ANA_ID: "Ana.Demo"}


async def test_update_refuses_a_username_taken_in_another_case(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    await _ensure(session_factory, _ana())
    bob = await _ensure(session_factory, _bob())
    bob.change_username("ANA")

    with pytest.raises(UsernameTaken):
        async with session_factory.begin() as session:
            await UserRepository(session).update(bob)

    assert await _usernames(engine) == {ANA_ID: "ana", BOB_ID: "bob"}


async def test_a_user_may_change_only_the_case_of_their_own_username(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    ana = await _ensure(session_factory, _ana())
    ana.change_username("ANA")

    async with session_factory.begin() as session:
        await UserRepository(session).update(ana)

    assert await _usernames(engine) == {ANA_ID: "ANA"}


@pytest.mark.parametrize(
    ("asked", "taken"), [("ana", True), ("AnA", True), ("bob", False)]
)
async def test_is_username_taken_ignores_case(
    session_factory: Factory, asked: str, taken: bool
) -> None:
    await _ensure(session_factory, _ana())

    async with session_factory() as session:
        assert await UserRepository(session).is_username_taken(asked) is taken
