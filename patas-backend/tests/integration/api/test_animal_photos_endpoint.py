"""US-13: photos go through Patas' own storage, within the size and origin limits."""

from collections.abc import AsyncIterator
from urllib.parse import parse_qs, urlparse

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import AUDIENCE, ISSUER, USER_ID, TokenIssuer

from patas_backend.auth.keys import StaticJwksKeyProvider
from patas_backend.config import Settings

PUBLIC = "https://pub-test.r2.dev"
OWN_PREFIX = f"{PUBLIC}/animals/{USER_ID}/"
FIVE_MB = 5 * 1024 * 1024


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _client(
    migrated_database_url: str, issuer: TokenIssuer, **storage: str
) -> AsyncIterator[httpx.AsyncClient]:
    # Imported here like in conftest: building the app needs TLS.
    from patas_backend.main import create_app

    settings = Settings(
        database_url=migrated_database_url,
        jwt_issuer=ISSUER,
        jwt_audience=AUDIENCE,
        **storage,
    )
    app = create_app(settings, StaticJwksKeyProvider(issuer.jwks()))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client
    await app.state.engine.dispose()


@pytest_asyncio.fixture
async def storage_client(
    engine: AsyncEngine, migrated_database_url: str, issuer: TokenIssuer
) -> AsyncIterator[httpx.AsyncClient]:
    # The credentials are fake: signing a URL happens offline.
    async for client in _client(
        migrated_database_url,
        issuer,
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret",
        aws_s3_endpoint_url="https://account.r2.cloudflarestorage.com",
        aws_storage_bucket_name="patas-test",
        public_upload_url=PUBLIC,
    ):
        yield client


@pytest_asyncio.fixture
async def no_storage_client(
    engine: AsyncEngine, migrated_database_url: str, issuer: TokenIssuer
) -> AsyncIterator[httpx.AsyncClient]:
    async for client in _client(
        migrated_database_url,
        issuer,
        aws_access_key_id="",
        aws_secret_access_key="",
        aws_s3_endpoint_url="",
        aws_storage_bucket_name="",
        public_upload_url="",
    ):
        yield client


async def test_the_upload_url_is_signed_for_the_owner_and_the_exact_size(
    storage_client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    response = await storage_client.post(
        "/animals/presigned-url",
        json={"content_type": "image/png", "size": 1234},
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["public_url"].startswith(OWN_PREFIX)
    assert body["public_url"].endswith(".png")
    query = parse_qs(urlparse(body["upload_url"]).query)
    assert "content-length" in query["X-Amz-SignedHeaders"][0].split(";")
    assert query["X-Amz-Expires"] == ["300"]


async def test_a_photo_over_five_megabytes_gets_no_upload_url(
    storage_client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    response = await storage_client.post(
        "/animals/presigned-url",
        json={"content_type": "image/jpeg", "size": FIVE_MB + 1},
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 422


async def test_only_jpeg_png_and_webp_can_be_uploaded(
    storage_client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    response = await storage_client.post(
        "/animals/presigned-url",
        json={"content_type": "image/gif", "size": 1234},
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 422


async def test_without_storage_settings_uploads_are_unavailable(
    no_storage_client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    response = await no_storage_client.post(
        "/animals/presigned-url",
        json={"content_type": "image/jpeg", "size": 1234},
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 503


async def test_own_uploaded_photos_are_published_and_listed(
    storage_client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    photo = f"{OWN_PREFIX}rex-1.jpg"

    response = await storage_client.post(
        "/animals",
        json={"name": "Rex", "species": "dog", "photo_urls": [photo]},
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 201
    catalog = (await storage_client.get("/animals")).json()
    assert catalog[0]["photo_urls"] == [photo]


async def test_a_photo_from_elsewhere_is_rejected_and_nothing_is_stored(
    storage_client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    response = await storage_client.post(
        "/animals",
        json={
            "name": "Rex",
            "species": "dog",
            "photo_urls": ["https://tracker.example/pixel.gif"],
        },
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 422
    assert (await storage_client.get("/animals")).json() == []


async def test_an_edit_cannot_add_a_photo_from_elsewhere(
    storage_client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    published = await storage_client.post(
        "/animals",
        json={"name": "Rex", "species": "dog"},
        headers=_bearer(issuer.token()),
    )

    response = await storage_client.put(
        f"/animals/{published.json()['id']}",
        json={
            "name": "Rex",
            "species": "dog",
            "photo_urls": ["https://tracker.example/pixel.gif"],
        },
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 422
