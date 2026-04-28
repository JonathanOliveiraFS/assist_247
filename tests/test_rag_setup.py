import asyncio
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from app.core.config import settings

async def populate_test_data(tenant_id: str):
    """
    Popula o ChromaDB com dados de teste para um cliente específico.
    """
    embeddings = OpenAIEmbeddings(
        api_key=settings.openai_api_key,
        model="text-embedding-3-small"
    )
    
    persist_directory = settings.chroma_persist_dir
    collection_name = f"cliente_{tenant_id}"
    
    print(f"--- Populando dados para {tenant_id} ---")
    
    # Documentos de exemplo (Matriz de uma clínica hipotética)
    docs = [
        Document(
            page_content="O horário de funcionamento da Clínica Integra é de segunda a sexta, das 08:00 às 18:00.",
            metadata={"source": "manual_clinica", "topic": "horarios"}
        ),
        Document(
            page_content="Aceitamos os convênios: Unimed, Bradesco Saúde e Amil.",
            metadata={"source": "manual_clinica", "topic": "convenios"}
        ),
        Document(
            page_content="A Clínica Integra fica localizada na Rua das Flores, 123, Centro.",
            metadata={"source": "manual_clinica", "topic": "localizacao"}
        )
    ]
    
    # Inicializa o Chroma e adiciona os documentos
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name=collection_name
    )
    
    print(f"Sucesso! {len(docs)} documentos adicionados à coleção {collection_name}.")
    print(f"Dados persistidos em: {persist_directory}")

if __name__ == "__main__":
    # Defina aqui o ID da instância que você usa no EvolutionAPI (ex: 'main_bot')
    TEST_TENANT_ID = "integra02" 
    asyncio.run(populate_test_data(TEST_TENANT_ID))
