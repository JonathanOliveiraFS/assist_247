import httpx
from app.config import settings

class EvolutionService:
    def __init__(self):
        self.base_url = settings.evolution_api_url.rstrip("/")
        self.api_key = settings.evolution_api_key

    async def send_text(self, instance: str, remote_jid: str, text: str):
        """Envia uma mensagem de texto via Evolution API."""
        url = f"{self.base_url}/message/sendText/{instance}"
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Payload corrigido para a Evolution API v2+
        payload = {
            "number": remote_jid,
            "text": text,
            "delay": 1200
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            
            # Adicionamos este print para ver exatamente o que a Evolution responde se der erro
            if response.status_code not in (200, 201):
                print(f"Detalhe do Erro Evolution API: {response.text}")
                
            response.raise_for_status()
            return response.json()