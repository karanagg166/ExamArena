from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:3000,https://exam-arena-mu.vercel.app"
    OPENAI_API_KEY: str | None = None
    REDIS_URL: str = "redis://localhost:6379/0"
    UPSTASH_REDIS_REST_URL: str | None = None
    UPSTASH_REDIS_REST_TOKEN: str | None = None
    STREAM_APP_ID: str = ""
    STREAM_API_KEY: str = ""
    STREAM_API_SECRET: str = ""
    COHERE_API_KEY: str | None = None
    COHERE_MODEL: str = "command-r-plus"
    QUESTION_IMPORT_MAX_FILE_MB: int = 15
    QUESTION_IMPORT_STORAGE_PATH: str = "uploads/question_imports"
    QUESTION_IMPORT_MAX_RETRIES: int = 3
    QUESTION_IMPORT_TIMEOUT_SECONDS: float = 60.0
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
