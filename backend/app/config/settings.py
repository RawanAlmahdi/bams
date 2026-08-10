from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "BAMS API"
    APP_VERSION: str = "1.0.0"

    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()