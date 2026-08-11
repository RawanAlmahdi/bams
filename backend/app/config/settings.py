from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "BAMS API"
    APP_VERSION: str = "1.0.0"

    FRONTEND_URL: str = "http://localhost:5173"
    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    INITIAL_ADMIN_USERNAME: str
    INITIAL_ADMIN_PASSWORD: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()