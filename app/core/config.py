from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "ByteSavor V3.0"
    debug: bool = True

    # MySQL
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_db: str = "bytesavor"

    # Redis
    redis_url: str = "redis://127.0.0.1:6379/0"

    # JWT
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24h

    # VLM
    vlm_api_url: str = ""
    vlm_api_key: str = ""
    vlm_model: str = "qwen3.5-27b-mlx"

    # LLM
    llm_api_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "qwen3.5-27b-mlx"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
