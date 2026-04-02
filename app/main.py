import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Request, BackgroundTasks
from app.bot_agent import process_chat
from app.evolution_service import EvolutionService
from pydantic import BaseModel, Field
from app.config import settings
from app.redis_manager import RedisManager

# --- Pydantic Models ---
class MessageData(BaseModel):
    remoteJid: str
    fromMe: bool
    pushName: Optional[str] = None
    message: dict = Field(default_factory=dict)

class EvolutionWebhook(BaseModel):
    event: str
    instance: str
    data: MessageData

# --- Lifespan Logic ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa o RedisManager
    app.state.redis_manager = RedisManager()
    try:
        await app.state.redis_manager.ping()
    except Exception as e:
        print(f"Erro ao conectar ao Redis: {e}")
    
    yield
    
    # Encerra a conexão
    await app.state.redis_manager.close()

app = FastAPI(
    title="Integra.ai - Motor de Tempo Real",
    lifespan=lifespan
)

# --- Helper function for Debounce Task ---
async def process_debounced_messages(instance: str, remote_jid: str, redis_manager: RedisManager):
    """Aguarda o delay do debounce, gera resposta via LLM e envia via Evolution API."""
    await asyncio.sleep(3)  # Delay do debounce
    messages = await redis_manager.consume_buffer(remote_jid)

    if messages:
        try:
            # 1. Gera a resposta usando o agente LangChain
            from app.bot_agent import process_chat
            # PASSAMOS O instance como tenant_id para o RAG
            response_text = await process_chat(messages, tenant_id=instance)

            # 2. Envia a resposta via EvolutionService
            from app.evolution_service import EvolutionService
            evolution_service = EvolutionService()
            await evolution_service.send_text(instance, remote_jid, response_text)

            print(f"Resposta enviada para {remote_jid}")
        except Exception as e:
            print(f"Erro ao processar/enviar mensagem: {e}")

# --- Routes ---
@app.get("/health")
async def health_check():
    redis_status = "offline"
    try:
        if await app.state.redis_manager.ping():
            redis_status = "online"
    except Exception:
        pass

    return {
        "status": "ok",
        "redis_connection": redis_status,
        "environment": settings.environment
    }

@app.post("/webhook")
async def evolution_webhook(payload: EvolutionWebhook, background_tasks: BackgroundTasks):
    # 1. Ignora mensagens enviadas pelo próprio bot ou que não sejam 'messages.upsert'
    if payload.event != "messages.upsert" or payload.data.fromMe:
        return {"status": "ignored"}

    remote_jid = payload.data.remoteJid
    
    # 2. Verifica se o atendimento humano está ativo (Human-in-the-Loop)
    if await app.state.redis_manager.is_human_active(remote_jid):
        print(f"Atendimento humano ativo para {remote_jid}. Ignorando bot.")
        return {"status": "human_active"}

    # 3. Tenta extrair o texto da mensagem (simplificado)
    message_text = payload.data.message.get("conversation") or \
                   payload.data.message.get("extendedTextMessage", {}).get("text")
    
    if not message_text:
        return {"status": "no_text_content"}

    # 4. Inicia o Debounce via Redis
    is_first_message = await app.state.redis_manager.add_to_buffer(remote_jid, message_text)
    
    if is_first_message:
        # AGORA PASSAMOS O payload.instance TAMBÉM!
        background_tasks.add_task(process_debounced_messages, payload.instance, remote_jid, app.state.redis_manager)

    return {"status": "queued"}
