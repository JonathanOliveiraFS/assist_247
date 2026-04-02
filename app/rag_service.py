from typing import List
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from app.config import settings

class RAGService:
    def __init__(self):
        """
        Inicializa o serviço de RAG com persistência e embeddings da OpenAI.
        """
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-3-small"
        )
        self.persist_directory = settings.chroma_persist_dir

    def _get_vectorstore(self, tenant_id: str) -> Chroma:
        """
        Instancia o Chroma para uma coleção específica do cliente (Multi-tenancy).
        """
        collection_name = f"cliente_{tenant_id}"
        
        return Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    async def get_relevant_documents(self, query: str, tenant_id: str, k: int = 4):
        """
        Recupera os documentos mais relevantes do banco vetorial de forma assíncrona.
        """
        vectorstore = self._get_vectorstore(tenant_id)
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        
        # Invoke assíncrono do retriever
        docs = await retriever.ainvoke(query)
        return docs

    def get_retriever(self, tenant_id: str, k: int = 4):
        """
        Retorna o objeto retriever do LangChain pronto para uso em Chains/Agents.
        """
        vectorstore = self._get_vectorstore(tenant_id)
        return vectorstore.as_retriever(search_kwargs={"k": k})
