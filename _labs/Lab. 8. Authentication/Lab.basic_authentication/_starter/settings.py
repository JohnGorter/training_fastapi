
from pydantic_settings import SettingsConfigDict, BaseSettings

class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    db_name: str = "fastapi_db"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()