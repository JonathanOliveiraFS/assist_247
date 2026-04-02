import asyncio
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Servidor de baixo nível - Sem logs automáticos para não quebrar o stdio
app = Server("mcp-mock-integra")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="agendar_reuniao",
            description="Agenda uma reunião ou compromisso. Recebe data e hora.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_hora": {"type": "string", "description": "Ex: amanhã às 15h"},
                },
                "required": ["data_hora"],
            },
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "agendar_reuniao":
        data_hora = arguments.get("data_hora", "não informada")
        return [
            types.TextContent(
                type="text",
                text=f"Sucesso: Reunião agendada para {data_hora}. O link foi enviado por e-mail."
            )
        ]
    return [types.TextContent(type="text", text="Erro: Ferramenta não encontrada.")]

async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())