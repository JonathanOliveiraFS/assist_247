import sys
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

class MCPManager:
    """
    Gerencia o ciclo de vida dos servidores MCP usando AsyncExitStack.
    Garante que os sub-processos não quebrem a thread principal do Uvicorn.
    """
    def __init__(self):
        self.tools = []
        self.stack = AsyncExitStack()
        
        # Caminhos absolutos mapeados para as pastas corretas
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.server_configs = {
            "agenda": os.path.join(base_dir, "mcp_servers", "mcp_agenda_clinica", "server.py"),
            "crm": os.path.join(base_dir, "mcp_servers", "mcp_crm_integra", "server.py"),
            "admin": os.path.join(base_dir, "mcp_servers", "admin", "server.py")
        }

    async def start(self):
        """Inicia o pool empilhando os contextos de forma segura."""
        print("\n" + "="*50)
        print("🚀 INICIANDO POOLING DE SERVIDORES MCP (ExitStack Mode)...")
        
        for name, script in self.server_configs.items():
            if not os.path.exists(script):
                print(f"⚠️ AVISO: Script MCP '{name}' não encontrado: {script}")
                continue

            params = StdioServerParameters(
                command=sys.executable,
                args=[script],
                env=os.environ.copy()
            )
            
            try:
                # O ExitStack gerencia o 'async with' dinamicamente sem travar o loop
                transport = await self.stack.enter_async_context(stdio_client(params))
                read, write = transport
                
                session = await self.stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                
                server_tools = await load_mcp_tools(session)
                self.tools.extend(server_tools)
                
                print(f"✅ Servidor MCP '{name}' conectado. Ferramentas ativas: {len(server_tools)}")
            
            except Exception as e:
                print(f"❌ ERRO no MCP '{name}' (Ignorado para não travar o bot): {e}")
        
        print(f"Total de ferramentas MCP no pool global: {len(self.tools)}")
        print("="*50 + "\n")

    async def stop(self):
        """Desempilha e fecha todos os recursos de uma vez."""
        print("🛑 Encerrando conexões persistentes MCP...")
        try:
            await self.stack.aclose()
            print("✅ Todos os sub-processos MCP finalizados.")
        except Exception as e:
            print(f"Aviso durante o encerramento: {e}")

    def get_tools(self):
        return self.tools