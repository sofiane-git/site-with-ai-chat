from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: SecretStr
    ollama_base_url: SecretStr
    ollama_model: str = "ministral-3:14b"

    azure_ai_inference_api_key: SecretStr
    azure_ai_inference_endpoint: SecretStr
    azure_ai_inference_model: str = "Mistral-Large-3"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
