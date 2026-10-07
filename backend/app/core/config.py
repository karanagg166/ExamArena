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
    COHERE_MODEL: str = "command-r-08-2024"
    CLOUDINARY_APIKEY: str | None = None
    CLOUDINARY_APISECRET: str | None = None
    CLOUDINARY_CLOUDNAME: str | None = None
    FILE_STORAGE_PROVIDER: str = "local"
    QUESTION_IMPORT_MAX_FILE_MB: int = 15
    QUESTION_IMPORT_STORAGE_PATH: str = "uploads/question_imports"
    QUESTION_IMPORT_MAX_RETRIES: int = 3
    QUESTION_IMPORT_TIMEOUT_SECONDS: float = 60.0
    ANSWER_KEY_IMPORT_MAX_FILE_MB: int = 15
    ANSWER_KEY_IMPORT_STORAGE_PATH: str = "uploads/answer_key_imports"
    ANSWER_KEY_IMPORT_MAX_RETRIES: int = 3
    ANSWER_KEY_IMPORT_TIMEOUT_SECONDS: float = 60.0

    # Search-Sphere RAG Microservice Integration
    SEARCH_SPHERE_URL: str = "http://localhost:8000"
    SEARCH_SPHERE_API_KEY: str | None = None
    SEARCH_SPHERE_CLIENT_ID: str = "exam_arena"
    SEARCH_SPHERE_TIMEOUT_SECONDS: float = 30.0

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
