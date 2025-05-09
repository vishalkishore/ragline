from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PDF QA System"
    debug: bool = Field(default=False)

    upload_dir: str = Field(default="./uploads")

    chroma_persist_directory: str = Field(default="./chroma_db")

    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")

    tokenizer_model: str = Field(default="BAAI/bge-small-en-v1.5")

    openai_api_key: str
    openai_model: str = Field(default="gpt-3.5-turbo")

    class Config:
        env_file = ".env"


settings = Settings()
