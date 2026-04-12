from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""

    AZURE_CLIENT_ID: str
    AZURE_TENANT_ID: str
    AZURE_CLIENT_SECRET: str
    DOMAIN: str = "intec.edu.ec"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Singleton de configuración cacheado."""
    return Settings()
