import json
import asyncio
import logging
from typing import Optional, List
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        self.redis = redis.from_url(settings.redis_url, decode_responses=True)

    async def close(self):
        await self.redis.close()

    async def ping(self):
        return await self.redis.ping()

    # --- Debounce Logic (Multi-tenancy Secured) ---
    async def add_to_buffer(self, tenant_id: str, remote_jid: str, message_text: str, delay: int = 3) -> bool:
        buffer_key = f"buffer:{tenant_id}:{remote_jid}"
        lock_key = f"lock:debounce:{tenant_id}:{remote_jid}"
        await self.redis.rpush(buffer_key, message_text)
        await self.redis.expire(buffer_key, 300)
        is_first = await self.redis.set(lock_key, "active", ex=delay, nx=True)
        return bool(is_first)

    async def consume_buffer(self, tenant_id: str, remote_jid: str) -> List[str]:
        buffer_key = f"buffer:{tenant_id}:{remote_jid}"
        messages = await self.redis.lrange(buffer_key, 0, -1)
        await self.redis.delete(buffer_key)
        return messages

    # --- Concurrency Control (Distributed Lock) ---
    async def acquire_processing_lock(self, tenant_id: str, remote_jid: str, ex: int = 60) -> bool:
        lock_key = f"lock:processing:{tenant_id}:{remote_jid}"
        return bool(await self.redis.set(lock_key, "true", ex=ex, nx=True))

    async def release_processing_lock(self, tenant_id: str, remote_jid: str):
        lock_key = f"lock:processing:{tenant_id}:{remote_jid}"
        await self.redis.delete(lock_key)

    # --- [NOVO] Chat History Management ---
    async def save_chat_history(self, tenant_id: str, remote_jid: str, role: str, content: str, max_messages: int = 12):
        """Salva uma mensagem no histórico persistente do Redis com limite de tamanho."""
        history_key = f"history:{tenant_id}:{remote_jid}"
        message_data = json.dumps({"role": role, "content": content})
        
        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.rpush(history_key, message_data)
            await pipe.ltrim(history_key, -max_messages, -1)  # Mantém apenas as últimas N mensagens
            await pipe.expire(history_key, 86400 * 7)         # Expira em 7 dias de inatividade
            await pipe.execute()

    async def get_chat_history(self, tenant_id: str, remote_jid: str) -> List[dict]:
        """Recupera o histórico de mensagens formatado para o Agente."""
        history_key = f"history:{tenant_id}:{remote_jid}"
        raw_history = await self.redis.lrange(history_key, 0, -1)
        
        history = []
        for msg in raw_history:
            try:
                history.append(json.loads(msg))
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Entrada de histórico corrompida ignorada para {remote_jid}: {msg}")
                continue
        return history

    # --- Human-in-the-Loop Logic (Multi-tenancy Secured) ---
    async def set_human_status(self, tenant_id: str, remote_jid: str, is_human: bool):
        status_key = f"status:human:{tenant_id}:{remote_jid}"
        await self.redis.set(status_key, "true" if is_human else "false", ex=86400)

    async def is_human_active(self, tenant_id: str, remote_jid: str) -> bool:
        status_key = f"status:human:{tenant_id}:{remote_jid}"
        status = await self.redis.get(status_key)
        return status == "true"

    # --- Metrics Tracking (TASK-7.3) ---
    async def increment_metric(self, tenant_id: str, metric_name: str, amount: int = 1):
        """Incrementa um contador diário para uma métrica específica do tenant."""
        from datetime import datetime
        day_str = datetime.now().strftime("%Y-%m-%d")
        metric_key = f"metrics:{tenant_id}:{day_str}:{metric_name}"
        await self.redis.incrby(metric_key, amount)
        await self.redis.expire(metric_key, 86400 * 30) # Mantém métricas por 30 dias
