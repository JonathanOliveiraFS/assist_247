import os
import asyncio
from datetime import datetime
from typing import Any
from notion_client import Client
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# Configuração do Servidor MCP Notion
server = Server("mcp-notion-crm")

# Configurações do Notion via variáveis de ambiente
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

# Instância do Cliente Notion
notion = Client(auth=NOTION_API_KEY) if NOTION_API_KEY else None

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Lista as ferramentas disponíveis."""
    return [
        types.Tool(
            name="registrar_lead",
            description="Registra um novo lead no banco de dados Notion CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Nome completo do lead"},
                    "telefone": {"type": "string", "description": "Telefone de contato"},
                    "resumo": {"type": "string", "description": "Resumo das observações/necessidades"},
                },
                "required": ["nome", "telefone", "resumo"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Executa as ferramentas do MCP."""
    if name == "registrar_lead":
        if not notion or not NOTION_DATABASE_ID:
            return [types.TextContent(type="text", text="Erro: Credenciais do Notion não configuradas.")]

        if not arguments:
            return [types.TextContent(type="text", text="Erro: Argumentos ausentes.")]

        nome = arguments.get("nome") or "Lead Sem Nome"
        telefone = arguments.get("telefone") or "Sem Telefone"
        resumo = arguments.get("resumo") or "Interesse em automações (via WhatsApp)"
        data_atual = datetime.now().isoformat()

        try:
            # Lógica de Inserção no Notion com Timeout de 5s
            # Usamos threads para a chamada síncrona do notion-client não bloquear o loop
            await asyncio.wait_for(
                asyncio.to_thread(
                    notion.pages.create,
                    parent={"database_id": NOTION_DATABASE_ID},
                    properties={
                        "Nome": {"title": [{"text": {"content": nome}}]},
                        "Telefone": {"rich_text": [{"text": {"content": telefone}}]},
                        "Status": {"select": {"name": "Contato"}},
                        "Serviço": {"select": {"name": "Configuração e Integração"}},
                        "Data contato": {"date": {"start": data_atual}},
                        "Observações": {"rich_text": [{"text": {"content": resumo}}]},
                    }
                ),
                timeout=5.0
            )
            
            return [
                types.TextContent(
                    type="text",
                    text=f"✅ Lead '{nome}' (Tel: {telefone}) registrado com sucesso no Notion CRM."
                )
            ]
        except asyncio.TimeoutError:
            print("TIMEOUT: Notion demorou muito para responder.", file=os.sys.stderr)
            return [
                types.TextContent(
                    type="text",
                    text="❌ Erro de Conexão: O Notion demorou muito para responder. Por favor, verifique se o banco de dados está acessível e tente novamente."
                )
            ]
        except Exception as e:
            error_msg = str(e)
            print(f"ERRO NOTION: {error_msg}", file=os.sys.stderr)
            if "API token is invalid" in error_msg:
                return [types.TextContent(type="text", text="❌ Erro de Autenticação: O token do Notion configurado no servidor é inválido ou expirou. Por favor, contate o suporte técnico.")]
            if "Could not find database" in error_msg:
                return [types.TextContent(type="text", text="❌ Erro de Configuração: O banco de dados do Notion não foi encontrado. Verifique o ID do banco de dados.")]
            
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Falha ao registrar lead: {error_msg}"
                )
            ]

    raise ValueError(f"Ferramenta desconhecida: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
