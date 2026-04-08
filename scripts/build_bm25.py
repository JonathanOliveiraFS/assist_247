import os
import pickle
import logging
from typing import List
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.retrievers import BM25Retriever
from app.config import settings

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Build_BM25")

def build_tenant_index(tenant_id: str):
    """
    Lê a pasta rag_data/docs/{tenant_id}/, faz o chunking e indexa em ChromaDB e BM25.
    """
    # 1. Caminhos
    base_docs_dir = settings.rag_docs_dir
    tenant_docs_dir = os.path.join(base_docs_dir, tenant_id)
    
    if not os.path.exists(tenant_docs_dir):
        logger.error(f"Pasta de documentos não encontrada para tenant '{tenant_id}': {tenant_docs_dir}")
        return False

    # 2. Carregamento de Documentos
    documents = []
    for file in os.listdir(tenant_docs_dir):
        file_path = os.path.join(tenant_docs_dir, file)
        try:
            if file.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif file.endswith(".docx"):
                loader = Docx2txtLoader(file_path)
                documents.extend(loader.load())
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo {file}: {e}")

    if not documents:
        logger.warning(f"Nenhum documento encontrado na pasta {tenant_docs_dir}")
        return False

    # 3. Fatiamento (Chunking)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(documents)
    logger.info(f"Processados {len(splits)} chunks para o tenant '{tenant_id}'")

    # 4. Salva no ChromaDB (Busca Semântica)
    embeddings = OpenAIEmbeddings(
        api_key=settings.openai_api_key,
        model="text-embedding-3-small"
    )
    collection_name = f"cliente_{tenant_id}"
    
    # Adicionando ao Chroma (vai persistir no diretório configurado)
    Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=settings.chroma_persist_dir
    )
    logger.info(f"Vetores salvos no ChromaDB para '{tenant_id}'")

    # 5. Salva o Arquivo Léxico (BM25 .pkl)
    bm25_retriever = BM25Retriever.from_documents(splits)
    bm25_path = os.path.join(settings.bm25_index_dir, f"{tenant_id}_index.pkl")
    
    os.makedirs(settings.bm25_index_dir, exist_ok=True)
    with open(bm25_path, "wb") as f:
        pickle.dump(bm25_retriever, f)
    
    logger.info(f"Índice BM25 salvo em: {bm25_path}")
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python scripts/build_bm25.py <tenant_id>")
        sys.exit(1)
    
    tenant_id = sys.argv[1]
    success = build_tenant_index(tenant_id)
    if success:
        print(f"✅ Índice construído com sucesso para o tenant: {tenant_id}")
    else:
        print(f"❌ Falha ao construir o índice para o tenant: {tenant_id}")
