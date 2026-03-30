# Message Debouncing & Redis Buffer

## Overview
WhatsApp messages often arrive in fragments. Integra.ai uses a Redis-based debounce to group these into a single processing unit, reducing LLM calls and context fragmentation.

## Implementation Workflow

### 1. Webhook Reception
FastAPI receives the message and pushes to a Redis list keyed by `chat_id`.

### 2. Debounce Logic
Use a `SETNX` (or a hash with timestamp) to manage the window (e.g., 2-3 seconds).

```python
import redis
import time

redis_client = redis.Redis(host='redis', port=6379, db=0)

async def buffer_message(chat_id, message_text):
    # 1. Store message in buffer
    redis_client.rpush(f"buffer:{chat_id}", message_text)
    
    # 2. Set/Update debounce timer
    # Key expires after 3 seconds. If it already exists, don't restart.
    # Alternatively, use a lua script for atomic updates.
    if not redis_client.exists(f"lock:{chat_id}"):
        redis_client.set(f"lock:{chat_id}", "active", ex=3)
        # Background task to wait 3 seconds and then process
        asyncio.create_task(process_buffer(chat_id))

async def process_buffer(chat_id):
    await asyncio.sleep(3.5) # Wait for buffer to settle
    # Collect all messages
    messages = redis_client.lrange(f"buffer:{chat_id}", 0, -1)
    redis_client.delete(f"buffer:{chat_id}")
    redis_client.delete(f"lock:{chat_id}")
    
    grouped_text = " ".join([m.decode('utf-8') for m in messages])
    # Send to LangChain agent...
```

## Considerations
- **Concurrency:** Ensure atomic operations using Redis Lua scripts if traffic is high.
- **Human-in-the-Loop:** Check the `status:{chat_id}` key *before* buffering to skip processing if an agent is active.
- **Max Delay:** Cap the total buffering time to 5-10 seconds to avoid frustration.
