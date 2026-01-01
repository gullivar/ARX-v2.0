from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "W-Intel v2.0"
    API_V1_STR: str = "/api/v2"
    
    # Database
    # Use absolute path to check logic
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/w_intel.db"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
