from typing import List, Optional, Annotated, TypedDict
import traceback
import operator
from datetime import datetime
import pytz
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage, ToolMessage
from langchain_core.messages import trim_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.core.config import settings
from app.services.rag_service import RAGService
from app.core.tenant_config import TENANT_CONFIG

# --- Definição do Estado do Agente (Harness State) ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    remote_jid: str
    tenant_id: str
    context: str 
    timestamp: str
    intent: str 
    is_human_transfer: bool
    summary: str # [TASK-H5] Memória de longo prazo consolidada

rag_service = RAGService()

# --- Nós do Grafo ---

async def summarize_history_node(state: AgentState):
    """
    [TASK-H5] Gera um resumo da conversa se o histórico for muito longo para manter a latência baixa.
    """
    messages = state["messages"]
    # Só resume se tiver um volume considerável (ex: > 12 mensagens)
    if len(messages) < 12:
        return {"summary": state.get("summary", "")}

    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model="gpt-4o-mini",
        temperature=0
    )
    
    existing_summary = state.get("summary", "")
    
    # Pega as mensagens mais antigas para resumir (exceto as últimas 6 que ficam no contexto imediato)
    messages_to_summarize = messages[:-6]
    
    summary_prompt = f"""
Como um assistente de IA, resuma a conversa abaixo de forma extremamente concisa. 
Foque em: Intenções do usuário, problemas resolvidos e informações importantes coletadas.
Se já houver um resumo anterior, consolide-o com as novas informações.

Resumo Anterior: {existing_summary if existing_summary else "Nenhum."}

Mensagens para resumir:
{messages_to_summarize}

Responda APENAS com o texto do novo resumo consolidado.
"""
    response = await llm.ainvoke([HumanMessage(content=summary_prompt)])
    return {"summary": response.content.strip()}

async def router_node(state: AgentState):
    """
    [TASK-H3] Nó Router Determinístico: Classifica a intenção do usuário.
    """
    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model="gpt-4o-mini",
        temperature=0
    )
    
    last_human_message = state["messages"][-1].content
    
    prompt = f"""
Classifique a intenção da seguinte mensagem do usuário em uma das categorias:
1. "support": Perguntas sobre a empresa, serviços, preços ou dúvidas técnicas.
2. "action": Solicitações de agendamento, cancelamento ou consulta de dados.
3. "human": O usuário solicitou explicitamente falar com um atendente, está muito frustrado, ou a IA não consegue ajudar.
4. "general": Saudações, agradecimentos ou conversas informais.

Mensagem: "{last_human_message}"

Responda APENAS com a palavra da categoria: support, action, human ou general.
"""
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    intent = response.content.strip().lower()
    
    if intent not in ["support", "action", "human", "general"]:
        intent = "support"
        
    return {"intent": intent, "is_human_transfer": intent == "human"}

async def rag_fetch_node(state: AgentState):
    """Busca RAG apenas se necessário."""
    user_input = state["messages"][-1].content
    tenant_id = state["tenant_id"]
    
    context_str = ""
    if tenant_id:
        docs = await rag_service.get_relevant_documents(user_input, tenant_id)
        if docs:
            context_str = "\n\n".join([doc.page_content for doc in docs])
            
    return {"context": context_str}

def make_call_model_node(tools: List):
    """Factory para criar o nó do modelo injetando as ferramentas sem poluir o estado."""
    async def call_model_node(state: AgentState):
        llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model="gpt-4o-mini",
            temperature=0
        )
        
        # Injeta ferramentas se for 'action' ou 'support'
        if state["intent"] in ["action", "support"] and tools:
            llm = llm.bind_tools(tools)
        
        config = TENANT_CONFIG.get(state["tenant_id"], {})
        
        intent_instruction = ""
        if state["intent"] == "general":
            intent_instruction = "- O usuário está apenas sendo cordial. Seja breve."
        elif state["intent"] == "human":
            intent_instruction = "- O usuário quer falar com um humano. Informe que está transferindo e encerre educadamente."

        # [TASK-H5] Otimização de Context Window
        # Filtra mensagens irrelevantes/antigas antes de enviar ao LLM
        trimmed_messages = trim_messages(
            state["messages"],
            strategy="last",
            max_tokens=1500, # Mantém histórico recente dentro de ~1500 tokens
            token_counter=llm, # Usa o próprio modelo para contar tokens
            allow_partial=True,
            include_system=False, # System prompt é injetado manualmente abaixo
        )

        summary = state.get("summary", "")
        summary_section = f"\nRESUMO DO HISTÓRICO ANTERIOR:\n{summary}\n" if summary else ""

        system_prompt = f"""
Você é {config.get('bot_name', 'Assistente')}, da {config.get('company_name', 'Empresa')}.
DATA/HORA: {state['timestamp']}
{summary_section}
CONTEXTO (RAG):
{state.get('context', 'Sem dados adicionais.')}

DIRETRIZES:
{intent_instruction}
- Se o usuário parecer frustrado ou pedir atendente humano, responda confirmando a transferência.
"""
        messages = [SystemMessage(content=system_prompt)] + trimmed_messages
        response = await llm.ainvoke(messages)
        
        return {"messages": [response]}
    return call_model_node

async def human_node(state: AgentState):
    """
    [TASK-H4] Nó de Transbordo Humano Nativo.
    """
    from app.core.redis_manager import RedisManager
    redis = RedisManager()
    await redis.set_human_status(state["tenant_id"], state["remote_jid"], True)
    
    last_msg = state["messages"][-1].content.lower()
    if "transfer" not in last_msg and "atendente" not in last_msg:
        transfer_msg = AIMessage(content="Certo, entendi. Estou transferindo você para um de nossos atendentes agora mesmo. Por favor, aguarde um momento.")
        return {"messages": [transfer_msg], "is_human_transfer": True}
        
    return {"is_human_transfer": True}

def route_after_intent(state: AgentState):
    if state["intent"] == "human": return "human"
    if state["intent"] == "support": return "rag_fetch"
    return "agent"

def should_continue(state: AgentState):
    if state.get("is_human_transfer"): return "human"
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "summarize" # [TASK-H5] Vai para o resumo antes de terminar

async def process_chat(messages: List[str], remote_jid: str, tenant_id: Optional[str] = None, tools: List = [], redis_manager = None) -> str:
    """
    EntryPoint para o Webhook: Orquestra o LangGraph com Checkpointing e HITL.
    """
    try:
        user_input = "\n".join(messages)
        tz_br = pytz.timezone('America/Sao_Paulo')
        timestamp_str = datetime.now(tz_br).strftime("%A, %d de %B de %Y, às %H:%M:%S")

        checkpoint_dir = "rag_data/checkpoints"
        os.makedirs(checkpoint_dir, exist_ok=True)
        db_path = os.path.join(checkpoint_dir, "graph_state.db")
        
        async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
            workflow = StateGraph(AgentState)
            
            workflow.add_node("router", router_node)
            workflow.add_node("rag_fetch", rag_fetch_node)
            workflow.add_node("agent", make_call_model_node(tools))
            workflow.add_node("human", human_node)
            workflow.add_node("summarize", summarize_history_node) # [TASK-H5]
            
            workflow.set_entry_point("router")
            
            workflow.add_conditional_edges(
                "router", route_after_intent,
                {"rag_fetch": "rag_fetch", "agent": "agent", "human": "human"}
            )
            
            workflow.add_edge("rag_fetch", "agent")
            workflow.add_edge("human", "summarize") # Resume mesmo após transferir (opcional)
            workflow.add_edge("summarize", END)

            if tools:
                tool_node = ToolNode(tools)
                workflow.add_node("tools", tool_node)
                workflow.add_edge("tools", "agent")
                
                workflow.add_conditional_edges(
                    "agent", should_continue,
                    {"tools": "tools", "human": "human", "summarize": "summarize"}
                )
            else:
                workflow.add_conditional_edges(
                    "agent", lambda x: "human" if x.get("is_human_transfer") else "summarize",
                    {"human": "human", "summarize": "summarize"}
                )

            config_tenant = TENANT_CONFIG.get(tenant_id, {})
            interrupt_list = ["tools"] if (config_tenant.get("approval_required") and tools) else []

            app_graph = workflow.compile(checkpointer=checkpointer, interrupt_before=interrupt_list)
            config = {"configurable": {"thread_id": remote_jid}}
            
            initial_state = {
                "messages": [HumanMessage(content=user_input)],
                "remote_jid": remote_jid,
                "tenant_id": tenant_id,
                "context": "",
                "timestamp": timestamp_str,
                "intent": "",
                "is_human_transfer": False,
                "summary": ""
            }

            result = await app_graph.ainvoke(initial_state, config=config)
            
            snapshot = await app_graph.aget_state(config)
            if snapshot.next:
                return "Sua solicitação (ação do sistema) está aguardando aprovação de um supervisor. Avisaremos assim que for processada."

            response_text = result["messages"][-1].content
            if redis_manager and tenant_id:
                await redis_manager.save_chat_history(tenant_id, remote_jid, "user", user_input)
                await redis_manager.save_chat_history(tenant_id, remote_jid, "assistant", response_text)

            return response_text

    except Exception as e:
        print(f"!!! ERRO NO HARNESS (H4) !!!: {e}")
        traceback.print_exc()
        return "Erro ao processar sua solicitação."
