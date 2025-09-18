from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    ENV: str = Field(
        default="development",
        description="Environment (development|staging|production)",
    )
    TZ: str = Field(default="Asia/Jakarta", description="Timezone")
    PORT: int = Field(default=8000, description="Server port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    DATABASE_URL: str | None = Field(
        default=None,
        description="SQLAlchemy connection string",
    )

    model_config = {"env_file": ".env"}


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
