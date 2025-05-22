"""
Application configuration.
Loads environment variables and provides settings for the application.
"""
import os
import sys
from pprint import pprint
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator, SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# --- Environment setup utility ---
def set_environment_from_args():
    os.environ["ENVIRONMENT"] = os.getenv("ENVIRONMENT", "local")
    for i, arg in enumerate(sys.argv):
        if arg in ("--env", "--environment") and i + 1 < len(sys.argv):
            os.environ["ENVIRONMENT"] = sys.argv[i + 1]
            print(f"ENVIRONMENT set from command-line: {os.environ['ENVIRONMENT']}")
            break
    print(f"ENVIRONMENT: {os.environ['ENVIRONMENT']}")


class Settings(BaseSettings):
    """Application settings."""

    # Basic app config (variables)
    APP_NAME: str = "Baid Server"
    DESCRIPTION: str = "Server for the baid agent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "local"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = ["http://localhost:3000"]

    # Variables (non-secret)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    LOCATION: Optional[str] = None
    DB_CONNECTION_SECRET: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[str] = None
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    PROJECT_ID: Optional[str] = None
    JWT_SECRET: Optional[str] = None

    # Secrets
    AGENT_ENGINE_ID: Optional[SecretStr] = None
    GOOGLE_CLIENT_SECRET: Optional[SecretStr] = None
    DB_PASSWORD: Optional[SecretStr] = None

    # Database config
    model_config = SettingsConfigDict(
        env_file=".env.local" if os.getenv("ENVIRONMENT", "local") == "local" else ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        # Ensure environment variables take precedence over .env files
        env_nested_delimiter="__",
        env_prefix="",
        env_ignore_empty=False,
    )

    def __init__(self, **data):
        super().__init__(**data)
        # Override settings with environment variables if they exist
        self._override_from_env()

    def _override_from_env(self):
        """Override settings with environment variables if they exist."""
        for field_name in self.model_fields:
            env_value = os.getenv(field_name)
            if env_value is not None:
                # Handle SecretStr fields
                if isinstance(getattr(self.__class__, field_name, None), property):
                    continue
                field_info = self.model_fields.get(field_name)
                if field_info and field_info.annotation is SecretStr:
                    setattr(self, field_name, SecretStr(env_value))
                # Handle CORS_ORIGINS special case
                elif field_name == "CORS_ORIGINS" and env_value:
                    if env_value.startswith("[") and env_value.endswith("]"):
                        import json
                        try:
                            setattr(self, field_name, json.loads(env_value))
                        except json.JSONDecodeError:
                            # Fall back to comma-separated parsing
                            setattr(self, field_name, [i.strip() for i in env_value.split(",")])
                    else:
                        setattr(self, field_name, [i.strip() for i in env_value.split(",")])
                # Handle boolean fields
                elif field_info and field_info.annotation is bool:
                    setattr(self, field_name, env_value.lower() in ("true", "1", "yes"))
                # Handle integer fields
                elif field_info and field_info.annotation is int:
                    try:
                        setattr(self, field_name, int(env_value))
                    except ValueError:
                        pass  # Skip if conversion fails
                # Handle all other fields
                else:
                    setattr(self, field_name, env_value)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    def print_variables(self):
        """Print all variables except secrets (mask secrets)."""
        out = {}
        for k, v in self.model_dump().items():
            if isinstance(getattr(self.__class__, k, None), property):
                continue
            if isinstance(v, SecretStr) or k in self._get_secret_fields():
                out[k] = "***SECRET***"
            else:
                out[k] = v
        pprint(out)

    def _get_secret_fields(self):
        return [name for name, field in self.model_fields.items() if field.annotation is SecretStr or (hasattr(field.annotation, '__origin__') and field.annotation.__origin__ is SecretStr)]


settings = Settings()