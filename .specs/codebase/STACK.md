# Stack Técnica - Integra.ai

## Core Backend
- **Linguagem:** Python >= 3.11
- **Framework Web:** FastAPI (uvicorn para ASGI)
- **Gestor de Dependências:** `uv` (identificado por `uv.lock`)

## IA & Orquestração
- **LLM:** OpenAI (GPT-4o ou similares)
- **Framework de IA:** LangChain & LangGraph (para fluxos de agentes complexos)
- **Protocolo de Ferramentas:** MCP (Model Context Protocol) via LangChain MCP Client
- **RAG Híbrido:** 
  - **Semântico:** ChromaDB (Vector Store)
  - **Léxico:** Rank-BM25 (Pickle files por cliente)

## Infraestrutura & Persistência
- **Mensageria/Cache/Estado:** Redis (usado para buffer de debounce e controle de 'human-in-the-loop')
- **Orquestração de Dados (ETL):** Kestra (pipelines YAML para processamento de documentos)
- **Containerização:** Docker & Docker Compose
- **WhatsApp Gateway:** EvolutionAPI (instância externa)

## Integrações
- **EvolutionAPI:** Webhooks (entrada) e REST API (saída)
- **MCP Servers:** Containers isolados para Agendas e CRMs
