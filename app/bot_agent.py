from typing import List, Optional
import sys
import os
import traceback
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 1. A NOVA IMPORTAÇÃO DO LANGCHAIN v1.0
from langchain.agents import create_agent
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import settings
from app.rag_service import RAGService

rag_service = RAGService()

# Calcula o caminho absoluto
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mcp_script_path = os.path.join(base_dir, "mcp_servers", "mcp_mock", "server.py")

mcp_server_params = StdioServerParameters(
    command=sys.executable,
    args=[mcp_script_path],
    env=os.environ.copy()
)

async def process_chat(messages: List[str], tenant_id: Optional[str] = None) -> str:
    try:
        llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model="gpt-4o-mini",
            temperature=0
        )
        
        user_input = "\n".join(messages)
        context_str = ""
        
        if tenant_id:
            docs = await rag_service.get_relevant_documents(user_input, tenant_id)
            if docs:
                context_str = "\n\n".join([doc.page_content for doc in docs])

        system_prompt = (
            "Você é o Integra.ai. Use o contexto para responder.\n"
            f"CONTEXTO:\n{context_str}\n\n"
            "Se precisar agendar, use a ferramenta 'agendar_reuniao'."
        )
        
        
        async with stdio_client(mcp_server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                mcp_tools = await load_mcp_tools(session)
                
                # 2. A CRIAÇÃO DO AGENTE NA v1.0 (Limpo e Direto)
                agent = create_agent(
                    model=llm, 
                    tools=mcp_tools, 
                    system_prompt=system_prompt
                )
                
                inputs = {"messages": [HumanMessage(content=user_input)]}
                result = await agent.ainvoke(inputs)
                
                return result["messages"][-1].content

    except Exception as e:
        print("\n" + "="*50)
        print(f"!!! ERRO CAPTURADO NO AGENTE !!!")
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensagem: {str(e)}")
        traceback.print_exc()
        print("="*50 + "\n")
        return "Erro técnico ao processar sua solicitação. Verifique os logs."