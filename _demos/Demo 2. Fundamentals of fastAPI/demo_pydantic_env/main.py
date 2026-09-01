from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class DatabaseSettings(BaseSettings):
    url: str = Field(validation_alias="DATABASE_URL")
    max_connections: int = Field(default=5, validation_alias="DB_MAX_CONNECTIONS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

class AppSettings(BaseSettings):
    debug: bool = False
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
settings = AppSettings()
# Access nested configuration
db_url = settings.database.url

print(f"Debug: {settings.debug}")
print(f"Database URL: {db_url}")