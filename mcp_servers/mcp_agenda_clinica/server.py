import os
import asyncio
from typing import Any
from pyairtable import Api
from mcp.server import Server, NotificationOptions
from mcp.server.stdio import stdio_server
import mcp.types as types

# Configuração do Servidor MCP
server = Server("mcp-airtable-bia")

# Configurações do Airtable vindas de variáveis de ambiente
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.environ.get("AIRTABLE_TABLE_NAME")

# Instância da API do Airtable
if AIRTABLE_API_KEY:
    airtable_api = Api(AIRTABLE_API_KEY)
    table = airtable_api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
else:
    table = None

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Lista as ferramentas disponíveis."""
    return [
        types.Tool(
            name="verificar_disponibilidade",
            description="Verifica se um horário já está ocupado no Airtable",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_hora": {"type": "string", "description": "Data e hora para verificar (formato exato no Airtable)"},
                },
                "required": ["data_hora"],
            },
        ),
        types.Tool(
            name="agendar_reuniao",
            description="Agenda uma reunião/atendimento na base do Airtable",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Nome completo do cliente"},
                    "telefone": {"type": "string", "description": "Telefone de contato"},
                    "data_hora": {"type": "string", "description": "Data e hora do agendamento (ISO format ou legível)"},
                },
                "required": ["nome", "telefone", "data_hora"],
            },
        )
    ]

async def _check_disponibilidade_async(data_hora: str) -> bool:
    """Verifica se o horário existe no Airtable com suporte a timeout."""
    if not table:
        return False
    
    formula = f"{{Data_Hora}} = '{data_hora}'"
    
    # Executa a chamada síncrona em uma thread separada com timeout
    try:
        records = await asyncio.wait_for(
            asyncio.to_thread(table.all, formula=formula),
            timeout=5.0
        )
        return len(records) > 0
    except asyncio.TimeoutError:
        raise RuntimeError("Tempo de resposta do Airtable excedido (Timeout 5s).")

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Executa as ferramentas do MCP."""
    if not table:
        return [types.TextContent(type="text", text="Erro: Variáveis de ambiente do Airtable não configuradas.")]

    if not arguments:
        return [types.TextContent(type="text", text="Erro: Argumentos ausentes.")]

    try:
        if name == "verificar_disponibilidade":
            data_hora = arguments.get("data_hora")
            if not data_hora:
                return [types.TextContent(type="text", text="Erro: data_hora é obrigatório.")]
            
            ocupado = await _check_disponibilidade_async(data_hora)
            status = "OCUPADO" if ocupado else "DISPONÍVEL"
            return [types.TextContent(type="text", text=f"O horário {data_hora} está {status}.")]

        if name == "agendar_reuniao":
            nome = arguments.get("nome")
            telefone = arguments.get("telefone")
            data_hora = arguments.get("data_hora")

            # Verificação de Conflito Interna
            if await _check_disponibilidade_async(data_hora):
                return [
                    types.TextContent(
                        type="text",
                        text=f"❌ Conflito de Horário: O horário {data_hora} já está reservado por outro cliente. Por favor, escolha outro horário."
                    )
                ]

            # Cria o registro no Airtable com timeout
            await asyncio.wait_for(
                asyncio.to_thread(table.create, {
                    "Nome": nome,
                    "Telefone": telefone,
                    "Data_Hora": data_hora
                }),
                timeout=5.0
            )
            
            return [
                types.TextContent(
                    type="text",
                    text=f"✅ Agendamento realizado com sucesso para {nome} em {data_hora}."
                )
            ]

    except asyncio.TimeoutError:
        return [
            types.TextContent(
                type="text",
                text="❌ Erro de Conexão: O serviço de agenda (Airtable) demorou muito para responder. Por favor, tente novamente em instantes."
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Erro operacional no MCP Airtable: {str(e)}"
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
