# Kestra Pipelines & Flow Design

## Overview
Kestra handles the "Motor de Backoffice" (ETL). It decouples document processing from the real-time API.

## Core Flow Patterns

### 1. Multi-tenant Ingestion
Every flow MUST accept a `customer_id` and `source_url/path`.

```yaml
id: atualizar_rag_cliente
namespace: integra.ai.rag

inputs:
  - id: customer_id
    type: STRING
  - id: file_url
    type: STRING

tasks:
  - id: download_doc
    type: io.kestra.plugin.core.http.Download
    uri: "{{ inputs.file_url }}"

  - id: process_rag
    type: io.kestra.plugin.scripts.python.Script
    beforeCommands:
      - pip install langchain langchain-openai chromadb rank_bm25
    script: |
      import os
      from langchain.text_splitter import RecursiveCharacterTextSplitter
      # Custom script for chunking, embedding, and saving to Chroma/BM25
      # (See references/indexing_logic.md for details)
```

## Best Practices
- **Concurrency:** Use `EachSequential` or `EachParallel` to process multiple documents for a single client.
- **Error Handling:** Implement `errors` tasks to notify the FastAPI Webhook if a crawl/index fails.
- **Triggers:** Use `Schedule` for periodic syncing (e.g., every 24h) or `Webhook` for real-time manual updates.
