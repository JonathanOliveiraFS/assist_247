import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# 1. Configura variáveis de ambiente ANTES de importar a 'app'
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["OPENAI_API_KEY"] = "sk-mock-key-for-testing"

# Adiciona o diretório raiz ao path
sys.path.append(os.getcwd())

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool

# --- Mocks Globais ---
mock_redis = AsyncMock()
mock_redis.is_human_active.return_value = False
mock_redis.set_human_status.return_value = None

def mock_llm_logic(messages):
    is_router = False
    if len(messages) == 1 and "Classifique a intenção" in messages[0].content:
        is_router = True
    
    last_content = messages[-1].content.lower()
    
    if is_router:
        # Extrai apenas a mensagem do usuário que está entre aspas no final do prompt
        import re
        match = re.search(r'Mensagem: "(.*)"', messages[-1].content)
        user_msg = match.group(1).lower() if match else last_content
        
        if "atendente" in user_msg or "human" in user_msg:
            return AIMessage(content="human")
        if "agende" in user_msg or "reunião" in user_msg:
            return AIMessage(content="action")
        return AIMessage(content="general")
    else:
        # Agent Node
        if "atendente" in last_content:
            return AIMessage(content="Entendido, vou chamar um atendente.")
        if "agende" in last_content:
            msg = AIMessage(content="Vou agendar sua reunião.")
            msg.tool_calls = [{"name": "agendar_reuniao_mock", "args": {"data_hora": "amanhã às 14h", "nome": "Jonathan"}, "id": "call_123"}]
            return msg
        return AIMessage(content="Olá!")

@tool
async def agendar_reuniao_mock(data_hora: str, nome: str):
    """Agenda uma reunião no sistema."""
    return f"REUNIÃO AGENDADA MOCK para {nome} em {data_hora}"

async def test_hitl_transfer():
    print("\n--- TESTE 1: TRANSBORDO PARA HUMANO ---")
    from app.services.bot_agent import process_chat
    
    remote_jid = "test_human_transfer@s.whatsapp.net"
    tenant_id = "integra_ai"
    messages = ["Quero falar com um atendente agora!"]
    
    with patch("app.services.bot_agent.ChatOpenAI") as mock_chat, \
         patch("app.core.redis_manager.RedisManager", return_value=mock_redis):
        
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(side_effect=mock_llm_logic)
        mock_chat.return_value = mock_instance
        
        response = await process_chat(
            messages=messages,
            remote_jid=remote_jid,
            tenant_id=tenant_id,
            tools=[]
        )
        
        print(f"RESPOSTA DO BOT: {response}")
        if "transferindo" in response.lower() or "atendente" in response.lower():
            print("✅ SUCESSO: Transbordo para humano detectado.")
        else:
            print("❌ FALHA: Mensagem de transbordo não enviada.")
        
        mock_redis.set_human_status.assert_called_with(tenant_id, remote_jid, True)

async def test_hitl_interrupt():
    print("\n--- TESTE 2: INTERRUPÇÃO PARA APROVAÇÃO (CRITICAL ACTION) ---")
    from app.services.bot_agent import process_chat
    from app.core.tenant_config import TENANT_CONFIG
    
    remote_jid = "test_interrupt@s.whatsapp.net"
    tenant_id = "integra_ai"
    messages = ["Agende uma reunião para amanhã às 14h no nome de Jonathan."]
    
    # Garante que approval_required está True para o teste
    TENANT_CONFIG[tenant_id]["approval_required"] = True
    
    with patch("app.services.bot_agent.ChatOpenAI") as mock_chat, \
         patch("app.core.redis_manager.RedisManager", return_value=mock_redis):
        
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(side_effect=mock_llm_logic)
        mock_instance.bind_tools.return_value = mock_instance
        mock_chat.return_value = mock_instance
        
        response = await process_chat(
            messages=messages,
            remote_jid=remote_jid,
            tenant_id=tenant_id,
            tools=[agendar_reuniao_mock]
        )
        
        print(f"RESPOSTA DO BOT: {response}")
        
        if "aguardando aprovação" in response:
            print("✅ SUCESSO: O grafo interrompeu corretamente antes da ferramenta crítica.")
        else:
            print(f"❌ FALHA: O grafo NÃO interrompeu. Resposta foi: {response}")

async def main():
    await test_hitl_transfer()
    await test_hitl_interrupt()

if __name__ == "__main__":
    asyncio.run(main())
