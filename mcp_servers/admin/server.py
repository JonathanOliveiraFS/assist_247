import os
import asyncio
from typing import Any
import redis.asyncio as redis
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
from datetime import datetime

# Importação relativa para usar o RedisManager do core (ajustando sys.path no startup se necessário)
# Por simplicidade no container MCP, usaremos o incremento direto via redis client
# ou recriaremos a lógica de métrica aqui.

# Configuração do Servidor MCP Admin
server = Server("mcp-admin-bia")

# Configurações do ambiente
REDIS_URL = os.environ.get("REDIS_URL")
EVOLUTION_API_URL = os.environ.get("EVOLUTION_API_URL", "").rstrip("/")
EVOLUTION_API_KEY = os.environ.get("EVOLUTION_API_KEY")
ADMIN_NUMBER = os.environ.get("ADMIN_NUMBER")
ADMIN_INSTANCE = os.environ.get("ADMIN_INSTANCE")

# Instância do Redis
r = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

async def increment_tenant_metric(tenant_id: str, metric_name: str):
    if not r: return
    day_str = datetime.now().strftime("%Y-%m-%d")
    metric_key = f"metrics:{tenant_id}:{day_str}:{metric_name}"
    await r.incr(metric_key)
    await r.expire(metric_key, 86400 * 30)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Lista as ferramentas administrativas."""
    return [
        types.Tool(
            name="solicitar_transbordo",
            description="Pausa o bot e solicita intervenção humana para este chat",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "string", "description": "O ID da instância/cliente (ex: integra02)"},
                    "remote_jid": {"type": "string", "description": "O ID do chat (ex: 5511999999999@s.whatsapp.net)"},
                    "nome": {"type": "string", "description": "Nome do cliente"},
                    "motivo": {"type": "string", "description": "Breve motivo da solicitação de transbordo"},
                },
                "required": ["tenant_id", "remote_jid", "nome", "motivo"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Executa as ferramentas do MCP Admin."""
    if name == "solicitar_transbordo":
        if not r or not EVOLUTION_API_KEY or not ADMIN_NUMBER:
            return [types.TextContent(type="text", text="Erro: Configurações de administração não encontradas.")]

        if not arguments:
            return [types.TextContent(type="text", text="Erro: Argumentos ausentes.")]

        tenant_id = arguments.get("tenant_id")
        remote_jid = arguments.get("remote_jid")
        nome = arguments.get("nome")
        motivo = arguments.get("motivo")

        try:
            # 1. Salva no Redis com Multi-tenancy (24h)
            status_key = f"status:human:{tenant_id}:{remote_jid}"
            await r.set(status_key, "true", ex=86400)

            # --- [TASK-7.3] Incrementa métrica de transbordo ---
            await increment_tenant_metric(tenant_id, "human_transfers")

            # 2. Notifica o administrador via Evolution API
            notificacao = (
                f"🚨 *SOLICITAÇÃO DE TRANSBORDO*\n\n"
                f"🏢 *Tenant:* {tenant_id}\n"
                f"👤 *Cliente:* {nome}\n"
                f"📱 *Chat ID:* {remote_jid}\n"
                f"📝 *Motivo:* {motivo}\n\n"
                f"O bot foi pausado por 24h para este chat."
            )

            url = f"{EVOLUTION_API_URL}/message/sendText/{ADMIN_INSTANCE}"
            headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
            payload = {"number": ADMIN_NUMBER, "text": notificacao}

            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()

            return [
                types.TextContent(
                    type="text",
                    text=f"✅ Transbordo solicitado com sucesso. O bot foi pausado e a equipe de atendimento notificada."
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Erro ao processar transbordo: {str(e)}"
                )
            ]

    raise ValueError(f"Ferramenta administrativa desconhecida: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
