import asyncio
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings

async def setup_bia():
    print("--- Iniciando Ingestão de PDF para a BIA (Integra.ai) ---")
    
    # 1. Calcula o caminho raiz para acessar a pasta rag_data
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(base_dir, "rag_data", "Guia_de_Conhecimento.pdf")
    persist_directory = os.path.join(base_dir, "rag_data", "chromadb")
    
    if not os.path.exists(pdf_path):
        print(f"Erro crítico: O arquivo não foi encontrado em {pdf_path}!")
        print("Por favor, garanta que o PDF está dentro da pasta 'rag_data'.")
        return

    # 2. Extração (Extract): Carrega o conteúdo do PDF
    print("Lendo o arquivo PDF...")
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    # 3. Transformação (Transform): Quebra o texto em fragmentos
    print("Processando e dividindo o texto em chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    splits = text_splitter.split_documents(docs)

    # 4. Configuração do Banco Vetorial
    tenant_id = "integra02" 
    collection_name = f"cliente_{tenant_id}"
    
    embeddings = OpenAIEmbeddings(
        api_key=settings.openai_api_key, 
        model="text-embedding-3-small"
    )
    
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )
    
    # 5. Carga (Load): Injeta os fragmentos no ChromaDB
    print(f"Injetando {len(splits)} fragmentos no banco vetorial...")
    await vector_store.aadd_documents(splits)
    
    print(f"Sucesso absoluto! A Matriz de Conhecimento da BIA foi atualizada no banco {collection_name}.")

if __name__ == "__main__":
    asyncio.run(setup_bia())