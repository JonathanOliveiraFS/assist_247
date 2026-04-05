import os
import pickle
import logging
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from app.config import settings

# Configuração de logs para auditoria do RAG
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG_Service")

class RAGService:
    def __init__(self):
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

    def _get_vectorstore(self, tenant_id: str) -> Chroma:
        """Instancia o banco vetorial isolado por tenant."""
        collection_name = f"cliente_{tenant_id}"
        return Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def _load_bm25_retriever(self, tenant_id: str) -> Optional[BM25Retriever]:
        """
        Tenta carregar o índice BM25 do disco para o tenant específico.
        [REQUISITO 3] Fallback gracioso se o índice não existir.
        """
        bm25_path = os.path.join(self.bm25_index_dir, f"{tenant_id}_index.pkl")
        
        if not os.path.exists(bm25_path):
            logger.warning(f"Índice BM25 não encontrado para tenant '{tenant_id}' em: {bm25_path}. Operando apenas com Busca Semântica.")
            return None
        
        try:
            with open(bm25_path, "rb") as f:
                # O arquivo pkl deve conter uma instância já treinada de BM25Retriever
                retriever = pickle.load(f)
                return retriever
        except Exception as e:
            logger.error(f"Erro ao carregar índice BM25 para tenant '{tenant_id}': {e}")
            return None

    async def get_relevant_documents(self, query: str, tenant_id: str, k: int = 4) -> List[Document]:
        """
        Executa uma Busca Híbrida (Ensemble) combinando ChromaDB e BM25.
        Aplica desduplicação e limita aos top k resultados mais relevantes.
        """
        # 1. Busca Semântica (Entendimento do contexto/significado)
        vectorstore = self._get_vectorstore(tenant_id)
        semantic_docs = await vectorstore.as_retriever(search_kwargs={"k": k}).ainvoke(query)
        
        # 2. Busca Léxica (Precisão de termos técnicos e nomes próprios)
        bm25_retriever = self._load_bm25_retriever(tenant_id)
        lexical_docs = []
        if bm25_retriever:
            try:
                # Executa busca léxica síncrona (comum no rank-bm25)
                lexical_docs = bm25_retriever.get_relevant_documents(query)[:k]
            except Exception as e:
                logger.error(f"Erro na execução da busca BM25: {e}")

        # 3. [REQUISITO 4] Fusão e Desduplicação dos resultados
        # Unimos as duas listas e filtramos duplicatas pelo conteúdo do texto.
        all_docs = semantic_docs + lexical_docs
        seen_contents = set()
        unique_docs = []

        for doc in all_docs:
            # Usamos o hash ou conteúdo exato para desduplicação
            content_hash = doc.page_content.strip()
            if content_hash not in seen_contents:
                unique_docs.append(doc)
                seen_contents.add(content_hash)

        # 4. Retorna os top K documentos consolidados
        return unique_docs[:k]

    def get_retriever(self, tenant_id: str, k: int = 4):
        """Retorna o retriever puramente vetorial para retrocompatibilidade."""
        vectorstore = self._get_vectorstore(tenant_id)
        return vectorstore.as_retriever(search_kwargs={"k": k})
