from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"
    SENTRY_DSN: str | None = None
    DATABASE_URL: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:3000,https://exam-arena-mu.vercel.app"
    OPENAI_API_KEY: str | None = None
    REDIS_URL: str = "redis://localhost:6379/0"
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
