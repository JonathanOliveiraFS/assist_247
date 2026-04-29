from typing import List, Optional, Annotated, TypedDict
import traceback
import operator
from datetime import datetime
import pytz
import os
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.core.config import settings
from app.core.redis_manager import RedisManager
from app.services.rag_service import RAGService
from app.core.tenant_config import TENANT_CONFIG
from app.services.evolution_service import EvolutionService
from app.core.mcp_manager import MCPManager

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    remote_jid: str
    tenant_id: str
    context: str 
    timestamp: str

async def router_node(state: AgentState):
    llm = ChatOpenAI(api_key=settings.openai_api_key, model="gpt-4o-mini", temperature=0)
    last_msg = state["messages"][-1].content
    prompt = f"Categorize intent (support, action, general): '{last_msg}'"
    res = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"intent": res.content.strip().lower()}

def make_rag_fetch_node(rag_service: RAGService):
    async def rag_fetch_node(state: AgentState):
        docs = await rag_service.get_relevant_documents(state["messages"][-1].content, state["tenant_id"])
        return {"context": "\n\n".join([d.page_content for d in docs]) if docs else ""}
    return rag_fetch_node

def make_call_model_node(tools: List):
    async def call_model_node(state: AgentState):
        llm = ChatOpenAI(api_key=settings.openai_api_key, model="gpt-4o-mini", temperature=0)
        if tools: llm = llm.bind_tools(tools)
        config = TENANT_CONFIG.get(state["tenant_id"], {})
        
        # Extrai o número do telefone do remote_jid (ex: 5511999999999@s.whatsapp.net -> 5511999999999)
        user_phone = state["remote_jid"].split("@")[0] if "@" in state["remote_jid"] else state["remote_jid"]
        
        sys_prompt = (
            f"Você é {config.get('bot_name', 'Assistente')}, um assistente virtual inteligente.\n"
            f"DATA ATUAL: {state['timestamp']}\n"
            f"ID DO USUÁRIO: {state['remote_jid']}\n"
            f"TELEFONE DO USUÁRIO: {user_phone}\n\n"
            f"DIRETRIZES:\n"
            f"- Use o telefone acima se o usuário disser 'pode ser esse número' ou similar.\n"
            f"- Ao registrar um lead, use o nome e telefone fornecidos ou extraídos.\n"
            f"CONTEXTO ADICIONAL:\n{state.get('context', 'Sem dados adicionais.')}"
        )
        
        # Envia apenas as últimas 10 mensagens para evitar quebra de sequência de tool_calls
        msgs = [SystemMessage(content=sys_prompt)] + state["messages"][-10:]
        res = await llm.ainvoke(msgs)
        return {"messages": [res]}
    return call_model_node

def should_continue(state: AgentState):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls: return "tools"
    return END

async def process_chat(messages: List[str], remote_jid: str, tenant_id: str, tools: List, redis_manager: RedisManager, rag_service: RAGService, evolution_service: EvolutionService) -> str:
    try:
        user_input = "\n".join(messages)
        timestamp = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M")
        db_path = "rag_data/checkpoints/graph_state.db"
        
        async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
            workflow = StateGraph(AgentState)
            workflow.add_node("rag_fetch", make_rag_fetch_node(rag_service))
            workflow.add_node("agent", make_call_model_node(tools))
            workflow.add_node("tools", ToolNode(tools))

            workflow.set_entry_point("rag_fetch")
            workflow.add_edge("rag_fetch", "agent")
            workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
            workflow.add_edge("tools", "agent")

            app_graph = workflow.compile(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": remote_jid}}
            
            result = await app_graph.ainvoke({"messages": [HumanMessage(content=user_input)], "remote_jid": remote_jid, "tenant_id": tenant_id, "timestamp": timestamp}, config=config)
            
            final_msg = result["messages"][-1].content
            await redis_manager.save_chat_history(tenant_id, remote_jid, "user", user_input)
            await redis_manager.save_chat_history(tenant_id, remote_jid, "assistant", final_msg)
            return final_msg
    except Exception as e:
        logger.error(f"Erro: {e}", exc_info=True)
        return "Tive um problema. Pode repetir?"

async def approve_action(*args, **kwargs):
    # Placeholder para manter compatibilidade, mas agora o fluxo é automático
    pass
