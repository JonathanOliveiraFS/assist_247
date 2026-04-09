# TASKS: Critérios de Aceite - Integra.ai

Este documento consolida as tarefas e critérios de aceite para a evolução do sistema Integra.ai.

## 1. Concluídos (Sprint Anterior)
- [x] **Humanização (Transbordo):** Sistema de pausa da IA para atendimento humano via Redis (24h) está funcional.
- [x] **Pooling de MCP:** O Agente LangChain gerencia múltiplos clientes MCP via `AsyncExitStack`.
- [x] **Filtro de Grupos:** Implementação inicial da lógica de ignorar mensagens de grupo.

## 2. Refinamento de Segurança e Lógica de Negócio (Sprint Atual)

### [TASK-01] Blindagem de Privacidade (app/main.py)
- [x] **Regra:** O bot deve processar exclusivamente mensagens privadas (`@s.whatsapp.net`).
- [x] **Critério de Aceite:** Na função `evolution_webhook`, se o `remote_jid` contiver `@g.us`, a mensagem deve ser ignorada imediatamente, retornando `{"status": "ignored_group"}`.

### [TASK-02] Lógica de Agenda e Mapeamento (mcp_servers/mcp_agenda_clinica/server.py)
- [x] **Regra:** Evitar choque de horários consultando o MCP do Airtable e mapear os dados corretamente.
- [x] **Critérios de Aceite:**
  1. Implementar a ferramenta `verificar_disponibilidade(data_hora: str)`, que faz um match na coluna `Data_Hora` do Airtable e retorna se há conflito.
  2. Na função `agendar_reuniao`, o valor recebido como `nome` no JSON deve ser salvo obrigatoriamente na coluna `Nome` (com N maiúsculo) do Airtable.
  3. A função `agendar_reuniao` deve chamar `verificar_disponibilidade` internamente e recusar o registro caso o horário já esteja ocupado.

### [TASK-03] RAG Dinâmico e Cache de Contexto no Fechamento
- [x] **Regra:** Buscar o contexto no RAG Híbrido (BM25 + Vetorial) apenas na primeira mensagem do cliente, salvando em cache para evitar retrabalho nas mensagens seguintes.
- [x] **Critérios de Aceite Técnicos:**
  1. Criar/atualizar `scripts/build_bm25.py` para processar a pasta `rag_data/docs` do respectivo tenant. Obs: Note que os pdfs ficarão na pasta docs dentro de rag_data.
  2. Implementar lógica condicional na chegada da mensagem: se o contexto já existe na instância, usá-lo imediatamente (Cenário A); se não existe (Cenário B - 1ª mensagem), disparar o Auto-Build e salvar em cache.
  3. **Tratamento de Timeout:** O Cenário B (Auto-Build) deve ser executado de forma assíncrona ou com tratamento de timeout adequado, garantindo que o tempo de leitura, chunking e indexação não derrube a requisição do webhook da Evolution API.

## 3. Sprint: Hardening de Infraestrutura (DevSecOps)

### [TASK-SEC-C3] Remoção de Hardcoded Secrets
- [x] **Regra:** Nenhuma chave ou segredo pode estar hardcoded no código-fonte.
- [x] **Critério de Aceite:** A chave do webhook do Kestra em `app/rag_service.py` foi substituída por `os.getenv("KESTRA_WEBHOOK_KEY", "fallback_key_aqui")`. Adicionar `KESTRA_WEBHOOK_KEY` ao `.env`.

### [TASK-SEC-C4] Fechamento de Portas Expostas
- [x] **Regra:** Serviços internos não devem expor portas no host de produção.
- [x] **Critério de Aceite:** Removidos os blocos `ports:` de `postgres` (5432) e `redis` (6379) no `docker-compose.yml`. Acesso ocorre exclusivamente via rede interna Docker.

### [TASK-SEC-A5] Remoção de Privilégios Excessivos (Kestra)
- [x] **Regra:** O container do Kestra não deve ter acesso ao daemon Docker do host.
- [x] **Critério de Aceite:** Removido o volume `- /var/run/docker.sock:/var/run/docker.sock` do serviço `kestra`. O Smart Cache com venv (`venv_kestra`) elimina a necessidade do Docker runner.

### [TASK-SEC-M2] Timeouts em Chamadas HTTP Externas
- [x] **Regra:** Todo `httpx.AsyncClient` deve ter timeout explícito para evitar travamento do bot.
- [x] **Critério de Aceite:** `evolution_service.py` → `timeout=15.0`. `rag_service.py` (Fire & Forget Kestra) → `timeout=3.0`.

### [TASK-SEC-A2] TTL do Distributed Lock (Race Condition)
- [x] **Regra:** O TTL de 60s do lock de processamento é insuficiente para tarefas complexas com MCPs.
- [x] **Critério de Aceite:** `app/main.py` → chamada `acquire_processing_lock(..., ex=120)` alterada para 120 segundos.

### [TASK-SEC-A3] Smart Cache Invalidation via mtime (RAG)
- [x] **Regra:** O cache em memória do BM25 não detecta quando o Kestra rebuild o arquivo `.pkl` no disco.
- [x] **Critério de Aceite:** `app/rag_service.py` → adicionado `self.bm25_mtimes = {}` no `__init__`. A função `_load_bm25_retriever` compara `os.path.getmtime(bm25_path)` com o mtime salvo; se o arquivo for mais recente, invalida o cache e recarrega. Sem bibliotecas externas (apenas `os` nativo).

## 4. Sprint: Sistema Nervoso Central & Operações (Kestra 1.3+)

### [TASK-7.1] Pipeline de RAG Assíncrono (Event-Driven)
- **Regra:** Transferir o "Auto-Build" do RAG do FastAPI para o Kestra usando gatilhos event-driven.
- **Critério de Aceite:** O RAG deve rodar em background via Kestra sem causar timeout no Webhook da Evolution API. O bot deve apenas sinalizar a necessidade ou aguardar a notificação de conclusão.

### [TASK-7.2] Deep Health Monitor
- **Regra:** Fluxo de monitoramento contínuo dos serviços críticos.
- **Critério de Aceite:** Fluxo no Kestra realizando pings em Redis, OpenAI API e instâncias da Evolution API, disparando alertas (ex: via WhatsApp/Email) em caso de falha.

### [TASK-7.3] Relatórios B2B Automatizados
- **Regra:** Agregação semanal de métricas de atendimento.
- **Critério de Aceite:** Fluxo agregando métricas por `tenant_id` no Notion/Airtable e enviando um resumo via Evolution API para os gestores.

### [TASK-7.4] FinOps - Governança de IA
- **Regra:** Rastreamento de custos e uso de tokens.
- **Critério de Aceite:** Job que rastreia o uso de tokens da OpenAI por `tenant_id`, mantendo histórico e disparando alertas ao atingir limites predefinidos.

### [TASK-7.5] CRM Proativo (Follow-up)
- **Regra:** Reativação de leads ociosos.
- **Critério de Aceite:** Trigger que busca leads sem interação recente no Notion e aciona o bot para um follow-up personalizado.
