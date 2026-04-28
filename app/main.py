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

from app.models.webhook import WebhookPayload

logger = logging.getLogger(__name__)


# --- Lifespan Logic: Gerenciamento de Estado Global ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Inicializa o RedisManager
    app.state.redis_manager = RedisManager()
    
    # 2. Inicialização Única dos MCPs (Pooling de Subprocessos)
    app.state.mcp_manager = MCPManager()
    await app.state.mcp_manager.start()

    # 3. Inicializa o EvolutionService (Singleton com pooling de conexões)
    app.state.evolution_service = EvolutionService()
    
    try:
        await app.state.redis_manager.ping()
        logger.info("Conexão com Redis estabelecida com sucesso.")
    except Exception as e:
        logger.error(f"ERRO Crítico de Conexão (Redis): {e}", exc_info=True)
    
    yield
    
    # Encerramento gracioso dos recursos
    logger.info("Limpando recursos no Shutdown (FastAPI Lifecycle)...")
    await app.state.mcp_manager.stop()
    await app.state.redis_manager.close()
    await app.state.evolution_service.close()

app = FastAPI(
    title="Integra.ai - Motor de Tempo Real (Memory & Time Edition)",
    lifespan=lifespan
)

# --- Helper function for Debounce Task ---
async def process_debounced_messages(
    instance: str, 
    remote_jid: str, 
    redis_manager: RedisManager, 
    mcp_manager: MCPManager,
    evolution_service: EvolutionService
):
    """Aguarda o delay do debounce, garante trava de concorrência e gera resposta via LLM."""
    await asyncio.sleep(3) 

    # 1. Verifica Transbordo Humano pós-debounce
    if await redis_manager.is_human_active(instance, remote_jid):
        logger.info(f"Transbordo detectado para {remote_jid}. Bot cancelado.")
        await redis_manager.consume_buffer(instance, remote_jid)
        return

    # 2. Trava de Processamento (Distributed Lock)
    if not await redis_manager.acquire_processing_lock(instance, remote_jid, ex=120):
        logger.warning(f"Chat {remote_jid} já em processamento. Ignorando tarefa redundante.")
        return

    try:
        messages = await redis_manager.consume_buffer(instance, remote_jid)

        if messages:
            try:
                # 3. Recupera ferramentas já carregadas no startup
                mcp_tools = mcp_manager.get_tools()

                # 4. Gera a resposta usando o agente (Injetando Memória e Ferramentas)
                from app.services.bot_agent import process_chat
                response_text = await process_chat(
                    messages, 
                    remote_jid=remote_jid, 
                    tenant_id=instance, 
                    tools=mcp_tools,
                    redis_manager=redis_manager # Passando o gerenciador para a memória
                )

                # 5. Envia a resposta via Evolution API (Usando Singleton Reutilizável)
                await evolution_service.send_text(instance, remote_jid, response_text)

                logger.info(f"Resposta enviada com sucesso para {remote_jid} (Instance: {instance})")
            except Exception as e:
                logger.error(f"Erro no processamento/envio para {remote_jid}: {e}", exc_info=True)
    finally:
        # Libera a trava para o próximo ciclo
        await redis_manager.release_processing_lock(instance, remote_jid)

# --- Routes ---
@app.get("/health")
async def health_check():
    redis_status = "offline"
    try:
        if await app.state.redis_manager.ping():
            redis_status = "online"
    except Exception as e:
        logger.error(f"Erro no Health Check (Redis Offline): {e}")

    return {
        "status": "ok",
        "redis_connection": redis_status,
        "mcp_tools_active": len(app.state.mcp_manager.get_tools()),
        "environment": settings.environment
    }

@app.post("/webhook")
async def evolution_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks):
    event = payload.event
    instance = payload.instance
    data = payload.data
    
    remote_jid = data.key.remoteJid
    from_me = data.key.fromMe

    if event != "messages.upsert" or from_me:
        return {"status": "ignored"}

    # --- [TASK-DEP-2.2] Validação de Tenant ID ---
    if instance not in TENANT_CONFIG:
        logger.warning(f"Instância desconhecida ignorada: {instance}")
        return {"status": "ignored_unknown_tenant"}

    # --- [TASK-01] Blindagem de Privacidade: Ignora Grupos ---
    if "@g.us" in remote_jid:
        logger.info(f"Mensagem de grupo ignorada: {remote_jid}")
        return {"status": "ignored_group"}

    if await app.state.redis_manager.is_human_active(instance, remote_jid):
        return {"status": "human_active"}

    if not data.message:
        return {"status": "no_message_content"}

    message_text = data.message.text
    
    if not message_text:
        return {"status": "no_text_content"}

    is_first_message = await app.state.redis_manager.add_to_buffer(instance, remote_jid, message_text)
    
    if is_first_message:
        background_tasks.add_task(
            process_debounced_messages, 
            instance, 
            remote_jid, 
            app.state.redis_manager,
            app.state.mcp_manager,
            app.state.evolution_service
        )

    return {"status": "queued"}

