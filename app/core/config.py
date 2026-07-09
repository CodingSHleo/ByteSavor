from pydantic import model_validator
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
    vlm_timeout_sec: int = 80  # Qwen VL 对 demo 大图可能需要 30s+，测试期避免误判为不可用

    # LLM
    llm_api_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "qwen3.5-27b-mlx"
    llm_timeout_sec: int = 15  # LLM 推理超时
    agent_llm_planner_enabled: bool = False
    agent_llm_judge_enabled: bool = False

    # Compatible aliases for DashScope/Qwen deployments. Do not put real keys in code.
    qwen_vl_api_url: str = ""
    qwen_vl_api_key: str = ""
    qwen_vl_model: str = ""

    @model_validator(mode="after")
    def apply_provider_aliases(self):
        if not self.vlm_api_url and self.qwen_vl_api_url:
            self.vlm_api_url = self.qwen_vl_api_url
        if not self.vlm_api_key and self.qwen_vl_api_key:
            self.vlm_api_key = self.qwen_vl_api_key
        if self.qwen_vl_model:
            self.vlm_model = self.qwen_vl_model
        return self

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
