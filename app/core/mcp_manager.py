import sys
import os
import logging
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

logger = logging.getLogger(__name__)

class MCPManager:
    """
    Gerencia o ciclo de vida dos servidores MCP usando AsyncExitStack.
    Garante que os sub-processos não quebrem a thread principal do Uvicorn.
    """
    def __init__(self):
        self.tools = []
        self.stack = AsyncExitStack()
        self.failed_mcps = [] # Rastreia falhas para diagnóstico
        
        # Caminhos absolutos mapeados para as pastas corretas
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.server_configs = {
            "agenda": os.path.join(os.path.dirname(base_dir), "mcp_servers", "mcp_agenda_clinica", "server.py"),
            "crm": os.path.join(os.path.dirname(base_dir), "mcp_servers", "mcp_crm_integra", "server.py"),
            "admin": os.path.join(os.path.dirname(base_dir), "mcp_servers", "admin", "server.py")
        }

    async def start(self):
        """Inicia o pool empilhando os contextos de forma segura."""
        logger.info("Iniciando pooling de servidores MCP (ExitStack Mode)...")
        self.failed_mcps = []
        
        for name, script in self.server_configs.items():
            if not os.path.exists(script):
                logger.warning(f"Script MCP '{name}' não encontrado: {script}")
                self.failed_mcps.append(name)
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
                
                logger.info(f"Servidor MCP '{name}' conectado com sucesso. Ferramentas ativas: {len(server_tools)}")
            
            except Exception as e:
                logger.error(f"Erro ao carregar servidor MCP '{name}': {e}", exc_info=True)
                self.failed_mcps.append(name)
        
        logger.info(f"Pool MCP inicializado. Total de ferramentas: {len(self.tools)}")
        if self.failed_mcps:
            logger.error(f"⚠️ Atenção: Falha ao carregar os seguintes MCPs: {self.failed_mcps}")

    async def stop(self):
        """Desempilha e fecha todos os recursos de uma vez."""
        logger.info("Encerrando conexões persistentes MCP...")
        try:
            await self.stack.aclose()
            logger.info("Todos os sub-processos MCP finalizados.")
        except Exception as e:
            logger.error(f"Aviso durante o encerramento do pool MCP: {e}", exc_info=True)

    def get_tools(self):
        return self.tools
