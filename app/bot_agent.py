from typing import List, Optional
import traceback
from datetime import datetime
import pytz
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Importação do agente LangChain (Customizado do projeto)
from langchain.agents import create_agent

from app.config import settings
from app.rag_service import RAGService

rag_service = RAGService()

async def process_chat(messages: List[str], remote_jid: str, tenant_id: Optional[str] = None, tools: List = [], redis_manager = None) -> str:
    """
    Processa a conversa com Memória Persistente, Noção Temporal e Foco em Experiência do Cliente.
    """
    try:
        llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model="gpt-4o-mini",
            temperature=0
        )
        
        user_input = "\n".join(messages)
        
        # 1. Recupera contexto do RAG
        context_str = ""
        if tenant_id:
            docs = await rag_service.get_relevant_documents(user_input, tenant_id)
            if docs:
                context_str = "\n\n".join([doc.page_content for doc in docs])

        # 2. Gerenciamento de Memória (Histórico do Redis)
        history_messages = []
        if redis_manager and tenant_id:
            chat_history = await redis_manager.get_chat_history(tenant_id, remote_jid)
            for msg in chat_history:
                if msg["role"] == "user":
                    history_messages.append(HumanMessage(content=msg["content"]))
                else:
                    history_messages.append(AIMessage(content=msg["content"]))

        # 3. Noção Temporal
        tz_br = pytz.timezone('America/Sao_Paulo')
        now = datetime.now(tz_br)
        timestamp_str = now.strftime("%A, %d de %B de %Y, às %H:%M:%S")

        system_prompt = (
            "Você é a BIA, assistente inteligente da Integra.ai.\n"
            f"ID DO CHAT ATUAL: {remote_jid}\n"
            f"TENANT ID (ID DA INSTÂNCIA): {tenant_id}\n"
            f"DATA/HORA ATUAL: {timestamp_str}\n\n"
            
            "🌟 FILOSOFIA DE ATENDIMENTO (EXPERIÊNCIA DO CLIENTE):\n"
            "- Fale com o cliente de forma humana, calorosa e personalizada. Use o nome dele se souber!\n"
            "- 🚫 PROIBIDO: Usar termos técnicos como 'lead', 'notion', 'airtable', 'base de dados', 'ferramenta', 'instância' ou 'registro efetuado'.\n"
            "- Em vez de 'Lead registrado', diga: 'Já anotei seu contato e seu interesse aqui comigo, [Nome]!'\n"
            "- Em vez de 'Agendamento realizado', diga: 'Tudo certo! Marquei nosso encontro para [Data/Hora]. Mal posso esperar!'\n\n"

            f"CONTEXTO DO CLIENTE (Sua Base de Conhecimento):\n{context_str}\n\n"

            "🎯 MATRIZ DE DECISÃO E FERRAMENTAS:\n"
            "1. [CONSULTA]: Antes de agendar qualquer coisa, use 'verificar_disponibilidade' para a data solicitada. Informe ao cliente se o horário está livre ou sugira alternativas se houver conflito.\n"
            "2. [AGENDA]: Após verificar que o horário está livre, use 'agendar_reuniao'. SEMPRE confirme o dia e hora exatos na sua resposta final.\n"
            "3. [INTERESSE]: Se o cliente demonstrar interesse mas não for um agendamento imediato, use 'registrar_lead'. Fale de forma acolhedora sobre isso.\n"
            "4. [TRANSBORDO]: Se o cliente estiver frustrado ou pedir explicitamente para falar com uma pessoa, use 'solicitar_transbordo' imediatamente. Passe o TENANT ID e REMOTE JID corretamente para esta ferramenta.\n\n"

            "⚠️ IMPORTANTE: Você tem acesso ao histórico da conversa acima. Use-o para não ser repetitivo e para lembrar o que o cliente já te disse."
        )
        
        # 4. Criação do Agente
        agent = create_agent(
            model=llm, 
            tools=tools, 
            system_prompt=system_prompt
        )
        
        # 5. Invocação
        inputs = {"messages": history_messages + [HumanMessage(content=user_input)]}
        result = await agent.ainvoke(inputs)
        response_text = result["messages"][-1].content
        
        # 6. Salva Interação na Memória
        if redis_manager and tenant_id:
            await redis_manager.save_chat_history(tenant_id, remote_jid, "user", user_input)
            await redis_manager.save_chat_history(tenant_id, remote_jid, "assistant", response_text)
        
        return response_text

    except Exception as e:
        print("\n" + "!"*50)
        print(f"!!! ERRO CRÍTICO NO AGENTE !!!")
        print(f"Mensagem: {str(e)}")
        traceback.print_exc()
        return f"Sinto muito, tive um probleminha técnico aqui. Pode repetir o que você gostaria de fazer?"
# Nota: No except, usei tenant_id como fallback mas o ideal seria o nome do cliente se disponível. 
# Como é um erro crítico, o mais importante é não travar.
