from typing import Annotated

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PATAS_", env_file=".env")

    # Default points at the local docker-compose database, which has no TLS.
    database_url: Annotated[
        str,
        Field(validation_alias=AliasChoices("DATABASE_URL", "PATAS_DATABASE_URL")),
    ] = (
        "postgresql+asyncpg://patas_admin:securepassword@localhost:5433/patas_db"
        "?ssl=disable"
    )
    jwks_url: str = "http://localhost:3000/api/auth/jwks"
    jwt_issuer: str = "http://localhost:3000"
    jwt_audience: str = "http://localhost:3000"

    # Cloudflare R2 / S3. boto3 reads AWS_ACCESS_KEY_ID and
    # AWS_SECRET_ACCESS_KEY natively from the environment.
    aws_access_key_id: Annotated[
        str,
        Field(validation_alias=AliasChoices("AWS_ACCESS_KEY_ID")),
    ] = ""
    aws_secret_access_key: Annotated[
        str,
        Field(validation_alias=AliasChoices("AWS_SECRET_ACCESS_KEY")),
    ] = ""
    aws_s3_endpoint_url: Annotated[
        str,
        Field(validation_alias=AliasChoices("AWS_S3_ENDPOINT_URL")),
    ] = ""
    aws_storage_bucket_name: Annotated[
        str,
        Field(validation_alias=AliasChoices("AWS_STORAGE_BUCKET_NAME")),
    ] = ""
    public_upload_url: Annotated[
        str,
        Field(
            validation_alias=AliasChoices(
                "PUBLIC_UPLOAD_URL", "PATAS_PUBLIC_UPLOAD_URL"
            )
        ),
    ] = ""

    @property
    def uploads_configured(self) -> bool:
        """Photo uploads need all of these; a missing one would give broken URLs."""
        return all(
            (
                self.aws_access_key_id,
                self.aws_secret_access_key,
                self.aws_s3_endpoint_url,
                self.aws_storage_bucket_name,
                self.public_upload_url,
            )
        )
