import asyncio
import os
import sys
from dotenv import load_dotenv # Importe a biblioteca dotenv

# Carrega as variáveis do arquivo .env localizado na raiz do projeto
load_dotenv()

# Adiciona o diretório atual ao sys.path para importar app
sys.path.append(os.getcwd())

from app.core.config import settings
from app.services.rag_service import RAGService
from app.core.redis_manager import RedisManager

async def test_hybrid_search():
    print("🚀 Iniciando teste de Busca Híbrida (BM25 + Chroma)...")
    
    # Injeta a chave dinamicamente a partir do arquivo .env
    # Se a variável não existir no .env, ele levanta um erro claro antes de rodar
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("A variável OPENAI_API_KEY não foi encontrada no arquivo .env!")
        
    settings.openai_api_key = api_key
    
    settings.chroma_persist_dir = "rag_data/chromadb"
    settings.bm25_index_dir = "rag_data/bm25_indexes"
    
    os.environ["CHROMA_PERSIST_DIR"] = "rag_data/chromadb"
    os.environ["BM25_INDEX_DIR"] = "rag_data/bm25_indexes"

    # ... restante do seu código (MockRedis, etc) continua igual ...