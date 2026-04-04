from typing import List, Optional
import sys
import os
import traceback
import asyncio
from datetime import datetime # Importação do relógio restaurada
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Importações LangChain e MCP
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

        # --- BLOCO PROTEGIDO: RELÓGIO E IDENTIDADE (NÃO ALTERAR) ---
        agora = datetime.now().strftime("%d/%m/%Y, %A, %H:%M")
        
        system_prompt = (
            "Você é a BIA, assistente inteligente da Integra.ai.\n"
            f"DATA E HORA ATUAL: {agora}\n"
            "IMPORTANTE: Use a data acima como referência absoluta para 'hoje', 'amanhã' ou datas relativas.\n\n"
            
            "SUA IDENTIDADE (ESTRATÉGIA COMERCIAL):\n"
            "- Você atua na configuração, integração técnica e suporte de atendentes virtuais de mercado.\n"
            "- Seu objetivo é liberar o cliente de tarefas repetitivas para foco em lucro e atendimento pessoal.\n\n"
            
            "CONTEXTO ESPECÍFICO DO CLIENTE:\n"
            f"{context_str}\n\n"
            
            "REGRAS DE OURO E USO DE FERRAMENTAS:\n"
            "1. Não invente dados; use apenas o manual oficial do cliente.\n"
            "2. Se o usuário quiser agendar uma reunião ou demonstração, use a ferramenta 'agendar_reuniao' (Airtable).\n"
            "3. Se for um novo contato (lead) interessado nos serviços, use 'registrar_lead' (Notion) com um breve resumo.\n"
            "4. Você pode e deve usar as DUAS ferramentas na mesma conversa se o cliente for novo e já quiser agendar algo.\n"
            "5. Sempre confirme o Nome, Telefone e Horário antes de finalizar as ações."
        )
        # -----------------------------------------------------------
        
        # Conectando aos dois servidores simultaneamente
        async with stdio_client(airtable_params) as (air_read, air_write), \
                   stdio_client(notion_params) as (not_read, not_write):
            
            async with ClientSession(air_read, air_write) as air_session, \
                       ClientSession(not_read, not_write) as not_session:
                
                await asyncio.gather(
                    air_session.initialize(),
                    not_session.initialize()
                )
                
                # Carrega as ferramentas de ambos os servidores
                air_tools = await load_mcp_tools(air_session)
                not_tools = await load_mcp_tools(not_session)
                
                # Combina todas as ferramentas
                all_tools = air_tools + not_tools
                
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