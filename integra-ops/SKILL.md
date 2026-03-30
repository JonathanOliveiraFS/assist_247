---
name: integra-ops
description: Expert in Kestra pipelines, ETL processes, and RAG indexing (ChromaDB + BM25). Manages document chunking, embedding generation, and automated multi-tenancy database updates.
---

# Integra Ops

## Overview
This skill provides expert guidance for the "Motor de Backoffice" of the **Integra.ai** project. It automates the ingestion, processing, and indexing of knowledge bases using Kestra and Python scripts.

## Core Operations

### 1. Kestra Pipeline Design (YAML Flows)
Orchestrate complex document processing workflows.
- **Reference:** See [kestra_flows.md](references/kestra_flows.md)
- **Constraint:** Flows MUST handle `customer_id` and be idempotent.

### 2. RAG Indexing & ETL Logic
Process documents for both semantic and lexical search.
- **Reference:** See [indexing_logic.md](references/indexing_logic.md)
- **Hybrid Strategy:** Always index for both ChromaDB and BM25 simultaneously to maintain consistency.

### 3. Automated Updates & Maintenance
Manage the lifecycle of the knowledge base.
- **Workflow:** 
    1. Detect document change (S3/Drive/Manual).
    2. Trigger Kestra flow.
    3. Update Vector/Lexical stores.
    4. Notify FastAPI via Webhook to reload memory.

## Workflow Decision Tree

### Updating a Knowledge Base?
1. **Source:** Is the source a single file or a folder? (Use `EachParallel` in Kestra for folders).
2. **Chunking:** Apply technical chunking (750 tokens, 150 overlap).
3. **Embed:** Generate OpenAI embeddings and update `collection_{customer_id}` in ChromaDB.
4. **Lexical:** Build/Update the `.pkl` index for BM25.
5. **Sync:** Notify the real-time API.

## Implementation Guidelines
- **Scalability:** Use Kestra workers for heavy embedding generation tasks.
- **Persistence:** Ensure all database paths are volume-mounted in Docker for persistent storage.
- **Logging:** Log successful index updates by `customer_id` and `timestamp`.

## Resources

### references/
- **[kestra_flows.md](references/kestra_flows.md):** YAML flow patterns.
- **[indexing_logic.md](references/indexing_logic.md):** Chunking and indexing scripts.
