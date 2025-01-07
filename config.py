import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database settings
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    
    # API settings
    API_HOST: str
    API_PORT: int
    DEBUG: bool
    
    # CORS settings
    ALLOWED_ORIGINS: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 