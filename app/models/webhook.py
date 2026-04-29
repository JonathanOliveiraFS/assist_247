from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

class WebhookKey(BaseModel):
    remoteJid: str
    fromMe: bool
    id: Optional[str] = None

class WebhookMessage(BaseModel):
    conversation: Optional[str] = None
    extendedTextMessage: Optional[Dict[str, Any]] = None

    @property
    def text(self) -> Optional[str]:
        """Extrai o texto independentemente do formato (simples ou estendido)."""
        if self.conversation:
            return self.conversation
        if self.extendedTextMessage:
            return self.extendedTextMessage.get("text")
        return None

class WebhookData(BaseModel):
    key: WebhookKey
    pushName: Optional[str] = None
    remoteJidAlt: Optional[str] = None
    senderPn: Optional[str] = None
    message: Optional[WebhookMessage] = None
    messageType: Optional[str] = None
    instanceId: Optional[str] = None
    source: Optional[str] = None

class WebhookPayload(BaseModel):
    event: str
    instance: str
    data: WebhookData
