from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
from app.rag_service import RAGService

# Instanciamos o RAGService uma única vez
rag_service = RAGService()

async def process_chat(messages: List[str], tenant_id: Optional[str] = None) -> str:
    """
    Instancia o LLM, recupera contexto do RAG e gera uma resposta fundamentada.
    """
    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model="gpt-4o-mini",
        temperature=0.7
    )
    
    # 1. Agrupa as mensagens do buffer em uma única string de busca
    user_input = "\n".join(messages)
    
    # 2. Busca contexto no RAG se houver um tenant_id
    context_str = ""
    if tenant_id:
        try:
            docs = await rag_service.get_relevant_documents(user_input, tenant_id)
            if docs:
                context_str = "\n\n".join([doc.page_content for doc in docs])
                print(f"Contexto recuperado para {tenant_id}: {len(docs)} fragmentos.")
        except Exception as e:
            print(f"Erro ao recuperar documentos do RAG: {e}")

    # 3. Define o prompt do sistema com o contexto injetado
    system_prompt = (
        "Você é o Integra.ai, um assistente corporativo útil e profissional. "
        "Utilize o contexto abaixo para responder à pergunta do usuário de forma precisa. "
        "Se a resposta não estiver no contexto, responda que não possui essa informação específica, "
        "mas tente ajudar com conhecimentos gerais se for apropriado, mantendo a postura profissional.\n\n"
        f"CONTEXTO RECUPERADO:\n{context_str}"
    )
    
    chat_messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]
    
    # 4. Gera a resposta usando o LLM
    response = await llm.ainvoke(chat_messages)
    return response.content
