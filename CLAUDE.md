# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Arquitetura Atual

O Integra.ai é um SaaS de atendimento via WhatsApp com arquitetura multi-tenant. Os serviços se comunicam via rede interna Docker (`docker-compose.yml`).

### Stack Principal

| Camada | Tecnologia | Container / Porta |
|---|---|---|
| API Gateway / Bot | FastAPI + LangChain | `integra_ai_bot:8000` |
| Comunicação WhatsApp | Evolution API | `evolution_api_integra:8080` |
| Cache / Memória / Lock | Redis | `redis_integra:6379` |
| Orquestrador Async | Kestra 1.3 LTS | `kestra_integra:8081` |
| Banco do Bot | PostgreSQL 15 | `postgres_integra:5432` |
| Banco do Kestra | PostgreSQL 15 | `postgres_kestra:5432` |
| Ferramentas Externas | Servidores MCP (stdio) | `mcp_agenda_clinica:8001`, `mcp_crm_integra:8002` |

### Fluxo de uma Mensagem (Happy Path)

```
WhatsApp → Evolution API → POST /webhook (FastAPI)
  → Filtra grupos (@g.us) e mensagens próprias
  → Verifica Transbordo Humano (Redis)
  → Buffer de Debounce (Redis, 3s)
  → process_debounced_messages (BackgroundTask)
    → Distributed Lock (Redis, TTL 60s)
    → RAG Híbrido (BM25 + ChromaDB)
    → Histórico (Redis)
    → LangChain Agent (gpt-4o-mini) + MCP Tools
    → Evolution API → WhatsApp
```

### Módulos-chave em `app/`

- `main.py` — Lifespan (init MCP pool + Redis), rota `/webhook` e `/health`. Ponto de entrada do fluxo.
- `bot_agent.py` — Função `process_chat`: monta System Prompt com RAG + histórico + contexto temporal, invoca o LangChain Agent.
- `mcp_manager.py` — Gerencia conexões MCP via `AsyncExitStack` (pooling persistente de subprocessos).
- `redis_manager.py` — Buffer de debounce, distributed lock, histórico de chat e flag de transbordo humano.
- `rag_service.py` — RAG Híbrido: BM25 (léxico) + ChromaDB (vetorial) por `tenant_id`.
- `tenant_config.py` — Configuração de persona e regras por tenant (nome do bot, empresa, `custom_rules`).

### Multi-tenancy

O `tenant_id` é derivado do campo `instance` do payload da Evolution API. Todo dado em Redis e ChromaDB é particionado por `tenant_id`. Novos tenants precisam de entrada em `TENANT_CONFIG` e documentos em `rag_data/docs/{tenant_id}/`.

### Kestra — Sistema Nervoso Central

Fluxos no namespace `io.integra.ai` (arquivos em `kestra/flows/`):
- `rag_sync.yaml` — Build assíncrono dos índices BM25 + ChromaDB (event-driven, evita timeout no webhook).
- `health_monitor.yaml` — Ping a cada 5 min em Redis, OpenAI, Evolution API.
- `b2b_reports.yaml` — Relatórios semanais por tenant no Notion/Airtable.
- `finops_tokens.yaml` — Rastreamento diário de uso de tokens por tenant.
- `crm_proactive.yaml` — Follow-up de leads ociosos via Notion.

Scripts Python executados pelo Kestra rodam em containers efêmeros (`runner: DOCKER`). O volume `./rag_data` é compartilhado entre o bot e o Kestra para acesso de baixa latência aos índices.

---

## Regra de Spec-Driven Development

**Nunca codar antes de documentar.** Para qualquer nova funcionalidade ou bugfix não trivial:

1. Escreva o critério de aceite em `TASKS.md` (o que deve funcionar, não como implementar).
2. Se envolver nova arquitetura, documente em `docs/` antes de abrir o editor.
3. Só então implemente, seguindo os critérios como checklist.

Esta regra está refletida no histórico de commits e nos arquivos de referência dos agentes (`integra-coder/`, `integra-reviewer/`, etc.).

---

## Negative Constraints — Prompts e Comportamento do Bot

As restrições abaixo estão hardcoded no System Prompt (`bot_agent.py`) e **não devem ser removidas ou suavizadas**:

- **Zero Tecniquês:** Proibido expor jargões técnicos ao cliente ("banco de dados", "ferramenta", "API", "transbordo", "prompt").
- **Zero Alucinação:** Nunca inventar dados de contato (nome, telefone). Se faltar, PERGUNTAR ao cliente.
- **Nunca Antecipar Sucesso:** Nunca confirmar agendamento antes de `agendar_reuniao` retornar com sucesso.
- **Nunca Responder em Grupos:** Mensagens com `@g.us` no `remote_jid` são rejeitadas imediatamente no webhook (retornam `{"status": "ignored_group"}`).
- **SOP de Agendamento:** Sempre seguir a ordem — verificar disponibilidade → coletar dados → executar agendamento.

---

## Comandos Docker

```bash
# Subir toda a infraestrutura em background
docker compose up -d

# Subir apenas serviços específicos (ex: bot + redis)
docker compose up -d bot redis

# Ver logs em tempo real do bot
docker compose logs -f bot

# Ver logs do Kestra
docker compose logs -f kestra

# Reconstruir a imagem do bot após mudanças em código
docker compose up -d --build bot

# Reconstruir um servidor MCP específico
docker compose up -d --build mcp-agenda

# Parar tudo
docker compose down

# Parar e apagar volumes (reset total — cuidado em produção)
docker compose down -v

# Executar comando dentro do container do bot
docker exec -it integra_ai_bot bash

# Forçar rebuild do índice RAG manualmente para um tenant
docker exec -it integra_ai_bot python scripts/build_bm25.py --tenant integra_ai
```

### Interfaces de Admin

- **Kestra UI:** `http://localhost:8081` — gerenciar e disparar fluxos manualmente.
- **Evolution API:** `http://localhost:8080` — gerenciar instâncias WhatsApp.
- **Bot Health:** `http://localhost:8000/health` — status de Redis e MCPs ativos.
