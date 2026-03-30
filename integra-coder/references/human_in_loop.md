# Human-in-the-Loop (HITL) State Management

## Overview
Integra.ai allows human agents to take over conversations. This state must be synchronized across all components (Webhook, Agent, Backoffice).

## Redis Schema
- `status:{chat_id}`: String value (`bot` or `human`).
- `human_takeover_at:{chat_id}`: Timestamp of when the bot was paused.

## Implementation Pattern

### 1. Webhook Filter
```python
def should_process(chat_id):
    status = redis_client.get(f"status:{chat_id}")
    if status == b"human":
        # Silently ignore to let the human agent interact
        return False
    return True
```

### 2. Agent Handover Tool
A LangChain tool that allows the LLM to trigger its own pause.

```python
from langchain.tools import tool

@tool
def request_human_handoff(chat_id: str, reason: str):
    """
    Sets the status to 'human' for a given chat_id. 
    Use this when the user is frustrated, requests a human, 
    or the query is out of scope.
    """
    redis_client.set(f"status:{chat_id}", "human")
    # Notify human agent via external API (e.g. EvolutionAPI / CRM)
    # notify_agent(chat_id, f"Takeover requested: {reason}")
    return "Handover initiated. I am now in standby."
```

## Best Practices
- **Auto-revert:** Consider an expiration on the `human` status (e.g., 2 hours) to avoid permanent "ghosting" if an agent forgets to close the ticket.
- **Context Injection:** When the human agent finishes, they should be able to send a "Back to Bot" command, which could trigger a summarization of the human interaction for the LLM.
