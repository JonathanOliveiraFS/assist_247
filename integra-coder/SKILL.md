---
name: integra-coder
description: Expert implementation for Integra.ai (FastAPI, LangChain, Redis). Specializes in WhatsApp message debouncing, Human-in-the-Loop state management, and Hybrid RAG (Chroma + BM25) ensemble patterns.
---

# Integra Coder

## Overview
This skill provides expert implementation guidance and code patterns for the **Integra.ai** project. It enforces the architectural decisions of utilizing Redis for state/buffer, FastAPI for real-time webhooks, and a Hybrid RAG strategy for high-precision retrieval.

## Core Expertise

### 1. Message Debouncing (Redis Buffer)
Implement logic to group multiple incoming WhatsApp messages from the same chat ID.
- **Reference:** See [debouncing.md](references/debouncing.md)
- **Goal:** Minimize LLM calls and aggregate message context.

### 2. Human-in-the-Loop (HITL)
Manage the transition between Bot and Human states in real-time.
- **Reference:** See [human_in_loop.md](references/human_in_loop.md)
- **Workflow:**
    1. Check `status:{chat_id}` in Redis on every incoming webhook.
    2. Provide a `request_human_handoff` tool to the LangChain Agent.
    3. Ensure the webhook ignores messages when state is `human`.

### 3. Hybrid RAG (Ensemble Pattern)
Combine semantic (ChromaDB) and lexical (BM25) search for technical precision.
- **Reference:** See [hybrid_rag.md](references/hybrid_rag.md)
- **Constraints:**
    - Always use `customer_id` for collection isolation (Multi-tenancy).
    - Favor weights around 0.6 (Semantic) and 0.4 (Léxical).

## Tooling & MCP Integration

### 1. Technical Grounding (Context7 MCP)
- **Ação:** Antes de implementar qualquer lógica de LangChain ou FastAPI, utilize o Context7 para verificar a sintaxe mais recente das bibliotecas.
- **Objetivo:** Garantir que o código gerado não utilize funções depreciadas e siga os contratos padronizados da Integra.ai.

### 2. Automation Validation (Playwright MCP)
- **Ação:** Para qualquer tarefa que envolva a criação de scrapers ou automação web, utilize o Playwright para validar os seletores e o fluxo de navegação antes de entregar o código final.
- **Workflow:**
    1. Escrever o script de automação.
    2. Executar o Playwright via MCP para testar o ambiente.
    3. Analisar falhas e auto-corrigir o código de automação.

## Workflow Decision Tree
1. Analyze: Use o Context7 para validar a viabilidade técnica da implementação com base nas docs atuais.

2. Develop: Escreva o código seguindo os padrões de async/await e Multi-tenancy.

3. Validate: Se houver automação web, execute o Playwright para garantir que a integração com sistemas externos não está quebrada.

4. Buffer & State: Integre a lógica final ao Redis para respeitar o status do atendimento (Bot vs Humano).

### Implementing a New Feature?
1. **Analyze:** Does it require a tool-call or external data? (Use MCP servers).
2. **Buffer:** Ensure the entry point (FastAPI) respects the Redis buffer logic.
3. **State:** Check if the feature should be active during a human takeover.
4. **Retrieve:** Use the `HybridRetriever` pattern for any knowledge-based query.

## Implementation Guidelines
- **Async First:** Use `async/await` for all FastAPI endpoints and LangChain calls.
- **Isolate Logic:** Keep the RAG logic in separate modules (`rag_hybrid.py`) and Redis management in `redis_manager.py`.
- **Typing:** Use Pydantic models for all data validation in FastAPI.

## Resources

### references/
- **[debouncing.md](references/debouncing.md):** Redis grouping patterns.
- **[human_in_loop.md](references/human_in_loop.md):** HITL states and handover tools.
- **[hybrid_rag.md](references/hybrid_rag.md):** EnsembleRetriever setup.
