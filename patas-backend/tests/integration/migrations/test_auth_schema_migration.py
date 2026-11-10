from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def test_patas_auth_schema_exists_for_better_auth(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        schema = await conn.scalar(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name = 'patas_auth'"
            )
        )

    assert schema == "patas_auth"
