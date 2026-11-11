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
