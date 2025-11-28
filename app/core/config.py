import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Configuración básica de la aplicación
    PROJECT_NAME: str = "DocuMind AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Configuración de directorios
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    TEMPLATE_DIR: str = "templates"
    API_BASE_URL: str = "http://localhost:8000"
    
    # DeepSeek API Configuration
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # Configuración de rate limiting
    MAX_TOKENS: int = 2000
    TIMEOUT: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()