import json
import asyncio
from typing import Optional, List
import redis.asyncio as redis
from app.config import settings

class RedisManager:
    def __init__(self):
        self.redis = redis.from_url(settings.redis_url, decode_responses=True)

    async def close(self):
        await self.redis.close()

    async def ping(self):
        return await self.redis.ping()

    # --- Debounce Logic ---
    async def add_to_buffer(self, remote_jid: str, message_text: str, delay: int = 3) -> bool:
        """
        Adiciona uma mensagem ao buffer de um chat. 
        Retorna True se for a primeira mensagem (iniciando o timer de debounce).
        """
        buffer_key = f"buffer:{remote_jid}"
        lock_key = f"lock:{remote_jid}"
        
        # Adiciona a mensagem à lista do Redis
        await self.redis.rpush(buffer_key, message_text)
        # Define um TTL para garantir limpeza em caso de falha
        await self.redis.expire(buffer_key, 60)

        # Tenta adquirir um "lock" simples de debounce
        is_first = await self.redis.set(lock_key, "active", ex=delay, nx=True)
        return bool(is_first)

    async def consume_buffer(self, remote_jid: str) -> List[str]:
        """Recupera e limpa todas as mensagens acumuladas no buffer."""
        buffer_key = f"buffer:{remote_jid}"
        messages = await self.redis.lrange(buffer_key, 0, -1)
        await self.redis.delete(buffer_key)
        return messages

    # --- Human-in-the-Loop Logic ---
    async def set_human_status(self, remote_jid: str, is_human: bool):
        """Define se o atendimento está com um humano ou com o bot."""
        status_key = f"status:human:{remote_jid}"
        # Expira em 24h para não poluir o Redis infinitamente
        await self.redis.set(status_key, "true" if is_human else "false", ex=86400)

    async def is_human_active(self, remote_jid: str) -> bool:
        """Verifica se o atendimento humano está ativo para este chat."""
        status_key = f"status:human:{remote_jid}"
        status = await self.redis.get(status_key)
        return status == "true"
