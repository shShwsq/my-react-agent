from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ai_chat"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    TTS_DEFAULT_VOICE_COSYVOICE_V35_FLASH: str = ""
    TTS_DEFAULT_VOICE_COSYVOICE_V35_PLUS: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
