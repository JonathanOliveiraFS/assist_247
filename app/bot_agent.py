from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings

async def process_chat(messages: List[str]) -> str:
    """Instancia o LLM, agrupa as mensagens do buffer e gera uma resposta."""
    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model="gpt-4o-mini",
        temperature=0.7
    )
    
    # Agrupa as mensagens do buffer em uma única string de contexto
    user_input = "\n".join(messages)
    
    chat_messages = [
        SystemMessage(content="Você é o Integra.ai, um assistente corporativo útil e profissional."),
        HumanMessage(content=user_input)
    ]
    
    response = await llm.ainvoke(chat_messages)
    return response.content
