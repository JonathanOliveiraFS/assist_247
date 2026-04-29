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
        
        # Log da mensagem sendo enviada para depuração
        logger.info(f"Enviando resposta para {remote_jid}: {text[:50]}...")

        # Payload corrigido para a Evolution API v2+
        payload = {
            "number": remote_jid,
            "text": text,
            "delay": 1200,
            "linkPreview": False
        }
        
        try:
            response = await self.client.post(url, json=payload)
            
            if response.status_code not in (200, 201):
                logger.error(f"Erro na Evolution API ({response.status_code}) para {remote_jid}: {response.text}")
                
            response.raise_for_status()
            logger.info(f"Mensagem enviada com sucesso para {remote_jid}")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro de status HTTP ao enviar mensagem para {remote_jid}: {e.response.text}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar mensagem via Evolution API para {remote_jid}: {e}", exc_info=True)
            raise

    async def send_buttons(self, instance: str, remote_jid: str, title: str, description: str, buttons: list, footer: str = ""):
        """Envia uma mensagem com botões interativos via Evolution API (v2 schema)."""
        url = f"{self.base_url}/message/sendButtons/{instance}"
        
        # O schema da v2.3+ exige displayText e id dentro de cada botão
        formatted_buttons = []
        for btn in buttons:
            formatted_buttons.append({
                "type": "reply",
                "displayText": btn.get("text", ""),
                "id": btn.get("id", "")
            })

        payload = {
            "number": remote_jid,
            "title": title,
            "description": description,
            "footer": footer,
            "buttons": formatted_buttons
        }
        
        try:
            response = await self.client.post(url, json=payload)
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao enviar botões: {e}")
            raise

    async def send_poll(self, instance: str, remote_jid: str, name: str, options: list, selectable_count: int = 1):
        """Envia uma enquete (Poll) como alternativa robusta aos botões no Baileys."""
        url = f"{self.base_url}/message/sendPoll/{instance}"
        
        payload = {
            "number": remote_jid,
            "name": name,
            "selectableOptionsCount": selectable_count,
            "options": options
        }
        
        try:
            response = await self.client.post(url, json=payload)
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao enviar enquete: {e}")
            raise

