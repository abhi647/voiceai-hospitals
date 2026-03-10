from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Voice AI Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # SQLite Database Config (MVP)
    SQLITE_DB: str = "sqlite:///./voice_ai.db"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # Default to SQLite for easy execution without Docker
        return self.SQLITE_DB
    
    # OpenAI & ElevenLabs
    OPENAI_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # LiveKit
    LIVEKIT_URL: Optional[str] = None
    LIVEKIT_API_KEY: Optional[str] = None
    LIVEKIT_API_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="allow")

settings = Settings()
