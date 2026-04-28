# Multi-tenancy Security Checklist

## 1. Redis Isolation
- [ ] Every Redis key includes a `customer_id` or `chat_id` prefix (e.g., `status:{customer_id}:{chat_id}`).
- [ ] Global keys (not scoped by customer) are strictly for internal system monitoring.
- [ ] No cross-customer keys are used in the same context/request.

## 2. Vector Store (ChromaDB) Isolation
- [ ] All queries use `collection_name=f"cliente_{customer_id}"`.
- [ ] No global `Chroma` instance without an explicit collection filter is used in the `agent.py`.
- [ ] `persist_directory` is clearly separated if using per-customer persistence.

## 3. BM25 (Lexical) Isolation
- [ ] BM25 index file load (`.pkl`) is strictly scoped by `customer_id`.
- [ ] Indices are never merged between different tenants.

## 4. API & Logging
- [ ] Logs never output the raw message content alongside the `customer_id` (PII protection).
- [ ] API responses strictly filter data belonging only to the authenticated `customer_id`.
