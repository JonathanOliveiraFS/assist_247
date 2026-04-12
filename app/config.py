from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # O Pydantic vai procurar essas variáveis no nosso .env
    openai_api_key: str = Field(..., env='OPENAI_API_KEY')
    
    chroma_persist_dir: str = Field(..., env='CHROMA_PERSIST_DIR')
    bm25_index_dir: str = Field(..., env='BM25_INDEX_DIR')
    rag_docs_dir: str = Field(default='/app/rag_data/docs', env='RAG_DOCS_DIR')
    
    evolution_api_url: str = Field(..., env='EVOLUTION_API_URL')
    evolution_api_key: str = Field(..., env='EVOLUTION_API_KEY')
    
    admin_number: str = Field(..., env='ADMIN_NUMBER')
    admin_instance: str = Field(..., env='ADMIN_INSTANCE')
    
    redis_url: str = Field(..., env='REDIS_URL')
    kestra_webhook_key: str = Field(default="fallback_key_aqui", env='KESTRA_WEBHOOK_KEY')

    environment: str = Field(default="development", env='ENVIRONMENT')

    # Configuração para ler o arquivo .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instanciamos as configurações para importar no resto do projeto
settings = Settings()