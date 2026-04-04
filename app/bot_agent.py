from typing import List, Optional
import sys
import os
import traceback
import asyncio
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

# Configuração dos múltiplos servidores MCP
airtable_script = os.path.join(base_dir, "mcp_servers", "airtable", "server.py")
notion_script = os.path.join(base_dir, "mcp_servers", "notion", "server.py")
admin_script = os.path.join(base_dir, "mcp_servers", "admin", "server.py")

airtable_params = StdioServerParameters(
    command=sys.executable,
    args=[airtable_script],
    env=os.environ.copy()
)

notion_params = StdioServerParameters(
    command=sys.executable,
    args=[notion_script],
    env=os.environ.copy()
)

admin_params = StdioServerParameters(
    command=sys.executable,
    args=[admin_script],
    env=os.environ.copy()
)

async def process_chat(messages: List[str], remote_jid: str, tenant_id: Optional[str] = None) -> str:
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
            "Você é o Integra.ai, um assistente corporativo inteligente para WhatsApp.\n"
            f"ID DO CHAT ATUAL: {remote_jid}\n\n"
            f"CONTEXTO DO CLIENTE:\n{context_str}\n\n"
            "DIRETRIZES DE OPERAÇÃO:\n"
            "1. Agendamentos: Use 'agendar_reuniao' (Airtable).\n"
            "2. Novos Leads: Use 'registrar_lead' (Notion CRM).\n"
            "3. REGRA DE OURO (Transbordo Humano): Se o cliente demonstrar frustração, pedir explicitamente para falar com um humano, "
            "ou se o assunto for complexo demais para sua base de conhecimento, use a ferramenta 'solicitar_transbordo'.\n"
            "   - Ao usar 'solicitar_transbordo', informe o remote_jid fornecido acima, o nome do cliente e o motivo.\n"
            "4. Seja sempre profissional, conciso e útil."
        )
        
        # Conectando aos três servidores simultaneamente
        async with stdio_client(airtable_params) as (air_read, air_write), \
                   stdio_client(notion_params) as (not_read, not_write), \
                   stdio_client(admin_params) as (adm_read, adm_write):
            
            async with ClientSession(air_read, air_write) as air_session, \
                       ClientSession(not_read, not_write) as not_session, \
                       ClientSession(adm_read, adm_write) as adm_session:
                
                await asyncio.gather(
                    air_session.initialize(),
                    not_session.initialize(),
                    adm_session.initialize()
                )
                
                # Carrega as ferramentas de todos os servidores
                air_tools = await load_mcp_tools(air_session)
                not_tools = await load_mcp_tools(not_session)
                adm_tools = await load_mcp_tools(adm_session)
                
                # Combina todas as ferramentas
                all_tools = air_tools + not_tools + adm_tools
                
                # Criação do Agente com multi-ferramentas
                agent = create_agent(
                    model=llm, 
                    tools=all_tools, 
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
