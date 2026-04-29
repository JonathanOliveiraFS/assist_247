import os
import pickle
import logging
import asyncio
import httpx
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from app.core.config import settings
from app.core.redis_manager import RedisManager

# Configuração de logs para auditoria do RAG
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, redis_manager: Optional[RedisManager] = None):
        """
        Inicializa o serviço de RAG Híbrido com persistência.
        Busca Semântica: ChromaDB (Vetorial)
        Busca Léxica: BM25 (Palavras-chave via Pickle)
        """
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-3-small"
        )
        self.persist_directory = settings.chroma_persist_dir
        self.bm25_index_dir = settings.bm25_index_dir
        self.redis = redis_manager or RedisManager()
        
        # Cache em memória para evitar IO excessivo
        self.bm25_retrievers = {}
        # Rastreia o mtime do arquivo .pkl por tenant para detectar atualizações do Kestra
        self.bm25_mtimes = {}

    def _get_vectorstore(self, tenant_id: str) -> Chroma:
        """Instancia o banco vetorial isolado por tenant."""
        collection_name = f"cliente_{tenant_id}"
        return Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    async def is_indexing(self, tenant_id: str) -> bool:
        """Verifica no Redis se o tenant está passando por um Rebuild do RAG."""
        key = f"rag:indexing:{tenant_id}"
        return await self.redis.redis.exists(key) > 0

    async def clear_indexing_status(self, tenant_id: str):
        """Remove a trava de indexação do Redis (chamado pelo Kestra ao finalizar)."""
        key = f"rag:indexing:{tenant_id}"
        await self.redis.redis.delete(key)
        logger.info(f"Status de indexação limpo para o tenant '{tenant_id}'.")

    async def _load_bm25_retriever(self, tenant_id: str) -> Optional[BM25Retriever]:
        """
        Tenta carregar o índice BM25 do disco para o tenant específico.
        [TASK-7.1] Se o índice não existir, aciona o Kestra de forma assíncrona.
        """
        bm25_path = os.path.join(self.bm25_index_dir, f"{tenant_id}_index.pkl")

        # Verifica Cache em memória com validação de mtime
        if tenant_id in self.bm25_retrievers:
            try:
                current_mtime = os.path.getmtime(bm25_path)
                if current_mtime <= self.bm25_mtimes.get(tenant_id, 0):
                    return self.bm25_retrievers[tenant_id]
                
                logger.info(f"Novo arquivo RAG detectado para '{tenant_id}'. Atualizando cache...")
                del self.bm25_retrievers[tenant_id]
                del self.bm25_mtimes[tenant_id]
            except OSError:
                del self.bm25_retrievers[tenant_id]
                self.bm25_mtimes.pop(tenant_id, None)
        
        if not os.path.exists(bm25_path):
            # Verifica se já existe um build em andamento para evitar spam de webhooks
            if await self.is_indexing(tenant_id):
                logger.info(f"Indexação já em curso para o tenant '{tenant_id}'. Aguardando Kestra...")
                return None

            logger.info(f"Índice ausente para '{tenant_id}'. Solicitando build ao Kestra...")
            
            # Marca no Redis que o build começou (TTL 10 min para evitar travamento em caso de erro no Kestra)
            await self.redis.redis.set(f"rag:indexing:{tenant_id}", "true", ex=600)

            async def trigger_kestra():
                try:
                    webhook_key = settings.kestra_webhook_key
                    kestra_base_url = settings.kestra_api_url.rstrip('/')
                    kestra_url = f"{kestra_base_url}/api/v1/executions/webhook/io.integra.ai/rag_sync/{webhook_key}"
                    async with httpx.AsyncClient() as client:
                        response = await client.post(kestra_url, json={"tenant_id": tenant_id}, timeout=3.0)
                        if response.status_code == 200:
                            logger.info(f"Kestra acionado para o tenant '{tenant_id}'.")
                        else:
                            logger.error(f"Falha ao acionar Kestra: {response.text}")
                except Exception as e:
                    logger.error(f"Erro de conexão com Kestra: {e}")

            asyncio.create_task(trigger_kestra())
            return None
        
        try:
            with open(bm25_path, "rb") as f:
                retriever = pickle.load(f)
                self.bm25_retrievers[tenant_id] = retriever
                self.bm25_mtimes[tenant_id] = os.path.getmtime(bm25_path)
                return retriever
        except Exception as e:
            logger.error(f"Erro ao carregar BM25 para '{tenant_id}': {e}")
            return None

    async def get_relevant_documents(self, query: str, tenant_id: str, k: int = 4) -> List[Document]:
        """Executa a Busca Híbrida (Ensemble) combinando ChromaDB e BM25."""
        vectorstore = self._get_vectorstore(tenant_id)
        semantic_docs = await vectorstore.as_retriever(search_kwargs={"k": k}).ainvoke(query)
        
        bm25_retriever = await self._load_bm25_retriever(tenant_id)
        lexical_docs = []
        if bm25_retriever:
            try:
                lexical_docs = bm25_retriever.invoke(query)[:k]
            except Exception as e:
                logger.error(f"Erro na busca BM25: {e}")

        # Fusão e Desduplicação
        all_docs = semantic_docs + lexical_docs
        seen_contents = set()
        unique_docs = []

        for doc in all_docs:
            content_hash = doc.page_content.strip()
            if content_hash not in seen_contents:
                unique_docs.append(doc)
                seen_contents.add(content_hash)

        return unique_docs[:k]

    def get_retriever(self, tenant_id: str, k: int = 4):
        """Retorna o retriever puramente vetorial para retrocompatibilidade."""
        vectorstore = self._get_vectorstore(tenant_id)
        return vectorstore.as_retriever(search_kwargs={"k": k})
