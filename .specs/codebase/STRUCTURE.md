# Estrutura do Projeto

```text
integra_ai_bot/
├── .specs/                     # Documentação de especificação (Spec-Driven)
├── app/                        # Motor Principal (FastAPI)
│   ├── main.py                 # Ponto de entrada e rotas de Webhook
│   ├── bot_agent.py            # Orquestração LangGraph/LangChain
│   ├── evolution_service.py    # Comunicação com EvolutionAPI
│   ├── redis_manager.py        # Buffer, Debounce e Estado de Atendimento
│   ├── config.py               # Configurações Pydantic
│   └── (rag_hybrid.py)         # Lógica de busca combinada (a ser validado)
├── kestra/                     # Pipelines de Dados
│   └── flows/                  # YAMLs do Kestra
├── mcp_servers/                # Ferramentas via Protocolo MCP
│   ├── mcp_agenda_clinica/     # Integração com agenda
│   └── mcp_crm_integra/        # Integração com CRM
├── rag_data/                   # Dados Persistentes do RAG (Volumes)
│   ├── chromadb/               # Banco vetorial
│   └── bm25_indexes/           # Índices léxicos (.pkl)
├── docker-compose.yml          # Orquestração de containers
├── Dockerfile                  # Build da imagem da API
└── pyproject.toml              # Dependências Python (uv)
```
