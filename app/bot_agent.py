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
from app.tenant_config import TENANT_CONFIG

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

        config = TENANT_CONFIG.get(tenant_id, {"bot_name": "Assistente", "company_name": "Empresa", "persona": "um atendente", "custom_rules": ""})

        system_prompt = f"""
Você é {config['bot_name']}, {config['persona']} da {config['company_name']}.

DADOS DO SISTEMA:

ID DO CHAT ATUAL: {remote_jid}

TENANT ID: {tenant_id}

DATA/HORA ATUAL: {timestamp_str}

CONTEXTO DO CLIENTE (Base de Conhecimento):
{context_str}

DIRETRIZES DE COMUNICAÇÃO E TOM DE VOZ
Aja de forma humana, natural e prestativa.

- Polidez em Primeiro Lugar: Sempre retribua saudações (Oi, Bom dia, Boa tarde ou Boa noite) antes de entregar a resposta de uma ferramenta.

{config['custom_rules']}

RESTRIÇÕES CRÍTICAS (NEGATIVE CONSTRAINTS)
NUNCA use termos técnicos ("banco de dados", "ferramenta", "prompt", "API").

- NUNCA use a palavra 'transbordo' ou relacionado a stack utilizada no projeto com o cliente. Se acionar a transferência para um humano, diga apenas algo como: 'Já avisei nossa equipe, um especialista vai falar com você por aqui em instantes'.

NUNCA invente informações de contato (nome, telefone). Se não souber, PARE e PERGUNTE ao cliente.

NUNCA diga que a reunião foi agendada antes da ferramenta agendar_reuniao retornar com sucesso.

NUNCA exponha os passos operacionais ou nomes de ferramentas ao cliente. Apenas aja.

PROTOCOLO ESTRITO DE AGENDAMENTO (SOP)
Siga OBRIGATORIAMENTE a ordem abaixo ao lidar com solicitações de agendamento. Pense passo a passo:

CONSULTA: Utilize OBRIGATORIAMENTE a ferramenta verificar_disponibilidade para o horário/data solicitado. Aguarde o retorno. Nunca assuma que um horário está livre.

COLETA: Se o horário estiver livre, verifique no histórico se você já possui o Nome completo e o Telefone do cliente. Se faltar algum dado, peça a informação de forma empática ANTES de tentar agendar.

EXECUÇÃO: Apenas quando o horário estiver validado (Etapa 1) E os dados de contato estiverem completos (Etapa 2), chame a ferramenta agendar_reuniao.
"""
        
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
