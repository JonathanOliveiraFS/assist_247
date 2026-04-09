import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Request, BackgroundTasks
from app.config import settings
from app.redis_manager import RedisManager
from app.mcp_manager import MCPManager


# --- Lifespan Logic: Gerenciamento de Estado Global ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Inicializa o RedisManager
    app.state.redis_manager = RedisManager()
    
    # 2. Inicialização Única dos MCPs (Pooling de Subprocessos)
    app.state.mcp_manager = MCPManager()
    await app.state.mcp_manager.start()
    
    try:
        await app.state.redis_manager.ping()
        print("✅ Conexão com Redis estabelecida.")
    except Exception as e:
        print(f"❌ ERRO Crítico de Conexão (Redis): {e}")
    
    yield
    
    # Encerramento gracioso dos recursos
    print("🧹 Limpando recursos no Shutdown...")
    await app.state.mcp_manager.stop()
    await app.state.redis_manager.close()

app = FastAPI(
    title="Integra.ai - Motor de Tempo Real (Memory & Time Edition)",
    lifespan=lifespan
)

# --- Helper function for Debounce Task ---
async def process_debounced_messages(instance: str, remote_jid: str, redis_manager: RedisManager, mcp_manager: MCPManager):
    """Aguarda o delay do debounce, garante trava de concorrência e gera resposta via LLM."""
    await asyncio.sleep(3) 

    # 1. Verifica Transbordo Humano pós-debounce
    if await redis_manager.is_human_active(instance, remote_jid):
        print(f"Transbordo detectado para {remote_jid}. Bot cancelado.")
        await redis_manager.consume_buffer(instance, remote_jid)
        return

    # 2. Trava de Processamento (Distributed Lock)
    if not await redis_manager.acquire_processing_lock(instance, remote_jid, ex=120):
        print(f"Chat {remote_jid} já em processamento. Ignorando tarefa redundante.")
        return

    try:
        messages = await redis_manager.consume_buffer(instance, remote_jid)

        if messages:
            try:
                # 3. Recupera ferramentas já carregadas no startup
                mcp_tools = mcp_manager.get_tools()

                # 4. Gera a resposta usando o agente (Injetando Memória e Ferramentas)
                from app.bot_agent import process_chat
                response_text = await process_chat(
                    messages, 
                    remote_jid=remote_jid, 
                    tenant_id=instance, 
                    tools=mcp_tools,
                    redis_manager=redis_manager # Passando o gerenciador para a memória
                )

                # 5. Envia a resposta via Evolution API
                from app.evolution_service import EvolutionService
                evolution_service = EvolutionService()
                await evolution_service.send_text(instance, remote_jid, response_text)

                print(f"Resposta enviada para {remote_jid} (Instance: {instance})")
            except Exception as e:
                print(f"Erro no processamento/envio: {e}")
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
    except Exception: pass

    return {
        "status": "ok",
        "redis_connection": redis_status,
        "mcp_tools_active": len(app.state.mcp_manager.get_tools()),
        "environment": settings.environment
    }

@app.post("/webhook")
async def evolution_webhook(payload: dict, background_tasks: BackgroundTasks):
    event = payload.get("event")
    instance = payload.get("instance")
    data = payload.get("data", {})

    key = data.get("key", {})
    from_me = key.get("fromMe", data.get("fromMe", False))
    remote_jid = key.get("remoteJid", data.get("remoteJid"))

    if event != "messages.upsert" or from_me:
        return {"status": "ignored"}

    if not remote_jid or not instance:
        return {"status": "error", "message": "Faltando instance ou remote_jid"}

    # --- [TASK-01] Blindagem de Privacidade: Ignora Grupos ---
    if "@g.us" in remote_jid:
        print(f"Mensagem de grupo ignorada: {remote_jid}")
        return {"status": "ignored_group"}

    if await app.state.redis_manager.is_human_active(instance, remote_jid):
        return {"status": "human_active"}

    message_obj = data.get("message", {})
    message_text = message_obj.get("conversation") or \
                   message_obj.get("extendedTextMessage", {}).get("text")
    
    if not message_text:
        return {"status": "no_text_content"}

    is_first_message = await app.state.redis_manager.add_to_buffer(instance, remote_jid, message_text)
    
    if is_first_message:
        background_tasks.add_task(
            process_debounced_messages, 
            instance, 
            remote_jid, 
            app.state.redis_manager,
            app.state.mcp_manager
        )

    return {"status": "queued"}
