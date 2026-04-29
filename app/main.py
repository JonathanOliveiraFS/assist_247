import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Request, BackgroundTasks
from app.core.config import settings
from app.core.redis_manager import RedisManager
from app.core.mcp_manager import MCPManager
from app.services.evolution_service import EvolutionService
from app.core.tenant_config import TENANT_CONFIG

from app.services.rag_service import RAGService
from app.models.webhook import WebhookPayload

logger = logging.getLogger(__name__)

# --- Lifespan Logic ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis_manager = RedisManager()
    app.state.mcp_manager = MCPManager()
    await app.state.mcp_manager.start()
    app.state.evolution_service = EvolutionService()
    app.state.rag_service = RAGService(redis_manager=app.state.redis_manager)
    try:
        await app.state.redis_manager.ping()
        logger.info("Conexão com Redis estabelecida.")
    except Exception as e:
        logger.error(f"Erro Redis: {e}")
    yield
    await app.state.mcp_manager.stop()
    await app.state.redis_manager.close()
    await app.state.evolution_service.close()

app = FastAPI(title="Integra.ai - Real-Time Engine", lifespan=lifespan)

# --- Helpers ---
async def handle_admin_action(body: dict, instance: str, action: str, client_jid: str, background_tasks: BackgroundTasks):
    """Auxiliar para processar cliques de botões ou votos de enquete do admin."""
    sender = body.get("sender", "")
    if sender != settings.admin_number:
        logger.warning(f"Tentativa de aprovação não autorizada por {sender}")
        return {"status": "unauthorized"}

    logger.info(f"Supervisor {action} ação para o cliente {client_jid}")
    from app.services.bot_agent import approve_action
    background_tasks.add_task(
        approve_action, client_jid, instance, action,
        app.state.evolution_service, app.state.redis_manager,
        app.state.rag_service, app.state.mcp_manager
    )
    return {"status": "approval_processed"}

async def process_debounced_messages(instance: str, remote_jid: str, redis_manager: RedisManager, mcp_manager: MCPManager, evolution_service: EvolutionService, rag_service: RAGService):
    await asyncio.sleep(3) 
    if await redis_manager.is_human_active(instance, remote_jid):
        await redis_manager.consume_buffer(instance, remote_jid)
        return
    if not await redis_manager.acquire_processing_lock(instance, remote_jid, ex=120):
        return
    try:
        messages = await redis_manager.consume_buffer(instance, remote_jid)
        if messages:
            await redis_manager.increment_metric(instance, "messages_processed")
            from app.services.bot_agent import process_chat
            response_text = await process_chat(
                messages, remote_jid=remote_jid, tenant_id=instance, 
                tools=mcp_manager.get_tools(), redis_manager=redis_manager, 
                rag_service=rag_service, evolution_service=evolution_service
            )
            await evolution_service.send_text(instance, remote_jid, response_text)
    finally:
        await redis_manager.release_processing_lock(instance, remote_jid)

# --- Routes ---
@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": settings.environment}

@app.post("/webhook")
async def evolution_webhook(payload: Request, background_tasks: BackgroundTasks):
    body = await payload.json()
    event = body.get("event")
    instance = body.get("instance")
    data = body.get("data", {})
    
    # 1. Eventos de Botão
    if event == "buttons.response":
        button_id = data.get("selectedButtonId", "")
        if ":" in button_id:
            action, client_jid = button_id.split(":", 1)
            return await handle_admin_action(body, instance, action, client_jid, background_tasks)

    # 2. Eventos de Enquete (Fallback Baileys)
    if event == "poll.vote":
        poll_name = data.get("pollName", "")
        if "🛡️ APROVAR AÇÃO" in poll_name and " para " in poll_name:
            client_jid = poll_name.split(" para ")[1].replace("?", "").strip()
            vote_options = data.get("vote", {}).get("selectedOptions", [])
            if vote_options:
                vote = vote_options[0].get("name", "")
                action = "approve" if "Aprovar" in vote else "reject"
                return await handle_admin_action(body, instance, action, client_jid, background_tasks)

    # 3. Mensagens
    if event != "messages.upsert": return {"status": "ignored_event"}
    key = data.get("key", {})
    remote_jid = key.get("remoteJid", "")
    if key.get("fromMe", False): return {"status": "ignored_from_me"}

    # Fix LID
    if "@lid" in remote_jid:
        if data.get("remoteJidAlt") and "@s.whatsapp.net" in data.get("remoteJidAlt"):
            remote_jid = data.get("remoteJidAlt")
        elif data.get("senderPn"):
            remote_jid = f"{data.get('senderPn').split(':')[0]}@s.whatsapp.net"

    if instance not in TENANT_CONFIG: return {"status": "ignored_unknown_tenant"}
    if "@g.us" in remote_jid: return {"status": "ignored_group"}
    if await app.state.redis_manager.is_human_active(instance, remote_jid): return {"status": "human_active"}

    msg_data = data.get("message", {})
    message_text = msg_data.get("conversation") or msg_data.get("extendedTextMessage", {}).get("text")
    if not message_text: return {"status": "no_text_content"}

    if await app.state.redis_manager.add_to_buffer(instance, remote_jid, message_text):
        background_tasks.add_task(process_debounced_messages, instance, remote_jid, app.state.redis_manager, app.state.mcp_manager, app.state.evolution_service, app.state.rag_service)

    return {"status": "queued"}
