import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class EvolutionService:
    """
    Serviço para comunicação com a Evolution API.
    Implementado como Singleton persistente no ciclo de vida da aplicação.
    """
    def __init__(self):
        self.base_url = settings.evolution_api_url.rstrip("/")
        self.api_key = settings.evolution_api_key
        # Reutiliza o cliente para manter conexões TCP ativas (pooling)
        self.client = httpx.AsyncClient(
            timeout=15.0,
            headers={
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }
        )

    async def close(self):
        """Fecha o cliente HTTP."""
        await self.client.aclose()
        logger.info("Conexão com Evolution API encerrada.")

    async def send_text(self, instance: str, remote_jid: str, text: str):
        """Envia uma mensagem de texto via Evolution API."""
        url = f"{self.base_url}/message/sendText/{instance}"
        
        # Payload corrigido para a Evolution API v2+
        payload = {
            "number": remote_jid,
            "text": text,
            "delay": 1200
        }
        
        try:
            response = await self.client.post(url, json=payload)
            
            if response.status_code not in (200, 201):
                logger.error(f"Erro na Evolution API ({response.status_code}): {response.text}")
                
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro de status HTTP ao enviar mensagem: {e.response.text}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar mensagem via Evolution API: {e}", exc_info=True)
            raise
