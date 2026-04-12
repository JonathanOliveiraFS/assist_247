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

## 5. Roteiro: RUMO AO DEPLOY 🚀



> Baseado na auditoria de 11/04/2026. Fases ordenadas por prioridade de bloqueio.

> Regra: nenhuma fase começa sem a anterior concluída (exceto F4, que corre em paralelo com F3).



---



### FASE 1 — Emergencial: Exposição de Secrets (< 1 dia)



### [TASK-DEP-1.1] Remoção do `.env` do Repositório Git ✅

- **Regra:** Nenhum secret com valor real pode existir no histórico do repositório.

- **Critérios de Aceite:**

  - [x] Executar `git rm --cached .env` e adicionar `.env` ao `.gitignore` — histórico purgado via `git filter-repo`; `.env` adicionado ao `.gitignore` (commit `b88ad90`)

  - [x] Confirmar com `git log --all -- .env` que o arquivo não aparece em commits futuros — `git log -- .env` retorna vazio

  - [x] Criar `.env.example` com todos os campos necessários e valores placeholder — criado com todos os campos do `.env` real substituídos por placeholders seguros

  - [x] `.env.example` versionado no repositório — commitado em `b88ad90`



### [TASK-DEP-1.2] Revogação e Rotação de todas as API Keys Expostas

- **Regra:** Todas as chaves expostas devem ser consideradas comprometidas e substituídas.

- **Critérios de Aceite:**

  - [ ] Revogar `OPENAI_API_KEY` no painel OpenAI e gerar nova

  - [ ] Revogar `GITHUB_TOKEN` no painel GitHub e gerar novo (escopo mínimo necessário)

  - [ ] Revogar `AIRTABLE_API_KEY` no painel Airtable e gerar nova

  - [ ] Revogar `NOTION_API_KEY` no painel Notion e gerar nova

  - [ ] Revogar `EVOLUTION_API_KEY` e gerar nova

  - [ ] Novas chaves salvas no `.env` local (nunca commitadas)

  - [ ] Validação: `docker compose up -d bot` sobe sem erros de autenticação



---



### FASE 2 — Bloqueadores de Segurança e Estabilidade (1–3 dias)



### [TASK-DEP-2.1] Autenticação no Redis

- **Regra:** O Redis não pode ser acessível sem senha dentro da rede Docker.

- **Critérios de Aceite:**

  - [x] Adicionar `REDIS_PASSWORD` ao `.env.example` — campo adicionado com placeholder; **adicionar manualmente ao `.env` local**

  - [x] Atualizar `docker-compose.yml`: `command: redis-server --requirepass ${REDIS_PASSWORD}` — feito

  - [x] Atualizar `REDIS_URL` em `.env.example` para `redis://:${REDIS_PASSWORD}@redis:6379/0`; `CACHE_REDIS_URI` da Evolution API também atualizada — **atualizar `.env` local manualmente**

  - [x] Validação: `docker exec redis_integra redis-cli ping` sem senha retorna `NOAUTH`

  - [x] Validação: `bot`, `kestra` e scripts conectam com sucesso após a mudança



### [TASK-DEP-2.2] Validação de Tenant ID no Webhook

- **Regra:** O endpoint `/webhook` só processa mensagens de instâncias registradas em `TENANT_CONFIG`.

- **Critérios de Aceite:**

  - [x] Em `app/main.py`, após extrair `instance` do payload, validar: `if instance not in TENANT_CONFIG: return {"status": "ignored_unknown_tenant"}`

  - [x] Log de warning emitido para instâncias desconhecidas (sem expor detalhes do payload)

  - [ ] Teste manual: payload com `instance: "tenant_inexistente"` retorna `{"status": "ignored_unknown_tenant"}` e HTTP 200

  - [ ] Teste manual: payload com `instance` válida continua processando normalmente



### [TASK-DEP-2.3] Consolidação dos Servidores MCP de Agenda

- **Regra:** Não pode existir mais de um servidor MCP registrando ferramentas com o mesmo nome.

- **Critérios de Aceite:**

  - [ ] Auditar `mcp_servers/airtable/server.py` vs `mcp_servers/mcp_agenda_clinica/server.py` e definir qual é canônico (critério: usa fórmula Airtable — mais determinístico)

  - [ ] Remover ou renomear o servidor conflitante; atualizar `mcp_manager.py` se necessário

  - [ ] Validação: `app.state.mcp_pool.get_tools()` não retorna nomes duplicados (verificar via `/health`)

  - [ ] Teste E2E: conversa de agendamento completa executa sem ambiguidade de ferramenta



### [TASK-DEP-2.4] Build Inicial dos Índices RAG para Tenant `integra_ai`

- **Regra:** O índice BM25 e a coleção ChromaDB devem existir antes do primeiro cliente interagir.

- **Critérios de Aceite:**

  - [ ] Executar `docker exec integra_ai_bot python scripts/build_bm25.py integra_ai` com sucesso

  - [ ] Arquivo `rag_data/bm25_indexes/integra_ai_index.pkl` existe e tem tamanho > 0

  - [ ] Coleção `cliente_integra_ai` existe no ChromaDB (`rag_data/chromadb/`)

  - [ ] Validação: endpoint `/health` não retorna aviso de índice ausente

  - [ ] Validação: consulta de teste retorna documentos relevantes sem disparar auto-build



### [TASK-DEP-2.5] Healthchecks em Todos os Serviços

- **Regra:** O Docker deve ser capaz de detectar e reportar serviços não saudáveis.

- **Critérios de Aceite:**

  - [x] `postgres`: `pg_isready` a cada 10s, 5 retries — feito

  - [x] `redis`: `redis-cli ping` a cada 10s, 5 retries — feito (com `-a ${REDIS_PASSWORD}`)

  - [x] `bot`: `curl -f http://localhost:8000/health` a cada 30s, `start_period: 40s` — feito; `curl` instalado no Dockerfile via `apt-get`

  - [x] `evolution-api`: `curl -f http://localhost:8080/` a cada 30s, `start_period: 40s`, 5 retries — feito

  - [x] `kestra`: `curl -f http://localhost:8080/health` a cada 30s, `start_period: 60s`, 5 retries — feito

  - [ ] Validação: `docker compose ps` mostra `(healthy)` para todos após startup

  - [x] `depends_on` do `bot` em relação a `postgres` e `redis` usa `condition: service_healthy` — feito; `evolution-api` atualizado para `condition: service_healthy`



### [TASK-DEP-2.6] Resource Limits no `docker-compose.yml`

- **Regra:** Nenhum container pode consumir recursos ilimitados no host de produção.

- **Critérios de Aceite:**

  - [ ] `bot`: `limits: {cpus: '2', memory: 2G}`, `reservations: {cpus: '0.5', memory: 512M}`

  - [ ] `postgres`: `limits: {cpus: '2', memory: 2G}`

  - [ ] `redis`: `limits: {cpus: '1', memory: 512M}`

  - [ ] `evolution-api`: `limits: {cpus: '2', memory: 2G}`

  - [ ] `kestra`: `limits: {cpus: '2', memory: 3G}`

  - [ ] Validação: `docker stats` após carga mostra uso dentro dos limites



### [TASK-DEP-2.7] Logging Driver com Rotação no `docker-compose.yml`

- **Regra:** Logs não podem crescer indefinidamente e precisam ser capturáveis em produção.

- **Critérios de Aceite:**

  - [ ] Todos os serviços com `logging: {driver: json-file, options: {max-size: 100m, max-file: "5"}}`

  - [ ] Validação: após 24h de operação, arquivos de log não excedem 500MB total



---



### FASE 3 — Qualidade de Código (3–7 dias)



### [TASK-DEP-3.1] Substituição Global de `print()` por `logging` Estruturado

- **Regra:** Zero chamadas `print()` em código de produção (`app/`, `mcp_servers/`).

- **Critérios de Aceite:**

  - [ ] Cada módulo usa `logger = logging.getLogger(__name__)` no topo

  - [ ] `logging.basicConfig()` removido de `rag_service.py` (deixar Uvicorn configurar)

  - [ ] Grep `print(` em `app/` e `mcp_servers/` retorna zero resultados

  - [ ] Logs de erro incluem `exc_info=True` onde aplicável

  - [ ] Validação: `docker compose logs bot` exibe logs com timestamp, nível e módulo



### [TASK-DEP-3.2] Pydantic Model para Payload do Webhook

- **Regra:** Todo input externo deve ser validado por schema antes de qualquer processamento.

- **Critérios de Aceite:**

  - [ ] Criar `class WebhookPayload(BaseModel)` com campos: `event: str`, `instance: str`, `data: dict`

  - [ ] Substituir `payload: dict` por `payload: WebhookPayload` em `evolution_webhook`

  - [ ] Validação: payload sem `instance` retorna HTTP 422 automaticamente (FastAPI)

  - [ ] Validação: payload malformado não chega ao processamento de mensagem



### [TASK-DEP-3.3] Corrigir Mutable Default Argument em `process_chat`

- **Regra:** Funções Python não podem ter listas ou dicionários mutáveis como default de parâmetro.

- **Critérios de Aceite:**

  - [ ] `tools: List = []` substituído por `tools: Optional[List] = None`

  - [ ] Corpo da função: `if tools is None: tools = []`

  - [ ] `redis_manager` recebe type hint correto: `Optional[RedisManager] = None`

  - [ ] Verificação: `mypy app/bot_agent.py` sem erros relacionados ao parâmetro



### [TASK-DEP-3.4] Corrigir Tratamento de Exceções Silenciosas Críticas

- **Regra:** Nenhuma exceção pode ser capturada e descartada sem logging e ação adequada.

- **Critérios de Aceite:**

  - [ ] `main.py`: `except Exception: pass` substituído por log de erro + `redis_status = "offline"`

  - [ ] `mcp_manager.py`: falha de carregamento de MCP emite `logger.error(..., exc_info=True)` e rastreia `failed_mcps`

  - [ ] `redis_manager.py`: `json.loads` envolto em try/except com log de warning por entrada corrompida

  - [ ] `bot_agent.py`: `result["messages"]` substituído por `result.get("messages", [])` com validação de lista não-vazia

  - [ ] Validação: desligar Redis com bot rodando → log de erro visível, sem crash silencioso



### [TASK-DEP-3.5] Singleton de `EvolutionService` e Reutilização de `httpx.AsyncClient`

- **Regra:** Conexões HTTP não devem ser abertas e fechadas a cada mensagem processada.

- **Critérios de Aceite:**

  - [ ] `EvolutionService` instanciado uma vez no `lifespan` e armazenado em `app.state.evolution_service`

  - [ ] `httpx.AsyncClient` criado no `__init__` e fechado no `lifespan` teardown

  - [ ] Background task acessa via `app.state.evolution_service` (não instancia localmente)

  - [ ] Validação: `docker stats` mostra file descriptors estáveis sob carga de 100 mensagens/min



### [TASK-DEP-3.6] Pinnar Versões das Imagens Docker

- **Regra:** Imagens com tag `:latest` são proibidas em produção.

- **Critérios de Aceite:**

  - [ ] `redis:latest` → `redis:7.2.4-alpine`

  - [ ] `evolution-api:latest` → versão exata do release atual

  - [ ] `kestra:latest-lts` → `kestra/kestra:X.Y.Z-lts` (versão exata)

  - [ ] Validação: `docker compose pull` não atualiza nenhuma imagem após pinnar



### [TASK-DEP-3.7] Timeouts Explícitos nos Servidores MCP

- **Regra:** Chamadas a APIs externas (Airtable, Notion) não podem bloquear indefinidamente.

- **Critérios de Aceite:**

  - [ ] `mcp_agenda_clinica/server.py`: operações Airtable envolvidas em `asyncio.wait_for(..., timeout=5.0)`

  - [ ] `mcp_crm_integra/server.py`: operações Notion envolvidas em `asyncio.wait_for(..., timeout=5.0)`

  - [ ] Timeout dispara `asyncio.TimeoutError` capturado, retorna mensagem de erro estruturada ao agente

  - [ ] Validação: simular lentidão da API → agente recebe erro em ≤6s, não trava



---



### FASE 4 — Resiliência Operacional (paralela à F3, concluir antes de escalar)



### [TASK-DEP-4.1] Flow Kestra: `health_monitor.yaml`

- **Regra:** Falhas em serviços críticos devem ser detectadas em até 5 minutos e notificadas.

- **Critérios de Aceite:**

  - [ ] Flow `io.integra.ai.health_monitor` com trigger schedule a cada 5 minutos

  - [ ] Tasks: ping Redis (`redis-cli ping`), ping OpenAI (`/v1/models`), ping Evolution API

  - [ ] Em caso de falha: envia alerta via Evolution API para número de admin configurado em env

  - [ ] Validação: derrubar Redis → alerta recebido em ≤10min



### [TASK-DEP-4.2] Kestra `rag_sync.yaml`: Timeout e Retry

- **Regra:** O flow de RAG deve ser resiliente a falhas transientes e não travar indefinidamente.

- **Critérios de Aceite:**

  - [ ] Adicionar `timeout: "30m"` ao task `execute_rag_script`

  - [ ] Adicionar `retry: {type: constant, interval: PT1M, maxAttempts: 3}`

  - [ ] Adicionar `errorHandler` com log de falha estruturado

  - [ ] Validação: forçar erro no script → Kestra retenta 3x e registra falha no histórico



### [TASK-DEP-4.3] Limite de Cache BM25 em Memória

- **Regra:** O cache de retrievers BM25 não pode crescer ilimitadamente.

- **Critérios de Aceite:**

  - [ ] `rag_service.py`: implementar `MAX_CACHED_RETRIEVERS = 50` com evição LRU via `collections.OrderedDict`

  - [ ] Quando cache atinge limite, entrada mais antiga é removida

  - [ ] Validação: instanciar 60 tenants distintos → memória não cresce além de ~50 retrievers ativos



### [TASK-DEP-4.4] Retry Logic em `EvolutionService.send_text()`

- **Regra:** Falhas transientes de rede não devem resultar em mensagens perdidas.

- **Critérios de Aceite:**

  - [ ] Adicionar `tenacity` ao `pyproject.toml`

  - [ ] Decorator `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))` em `send_text`

  - [ ] Retry apenas em `httpx.NetworkError` e `httpx.TimeoutException` (não em 4xx)

  - [ ] Validação: simular queda de rede de 3s → mensagem entregue após retry, sem erro visível ao cliente



---



### FASE 5 — Gate de Lançamento (checklist final pré-go-live)



### [TASK-DEP-5.1] Smoke Test End-to-End em Staging

- **Regra:** O sistema completo deve funcionar sem intervenção manual em ambiente limpo.

- **Critérios de Aceite:**

  - [ ] `docker compose down -v && docker compose up -d` em máquina limpa sem erros

  - [ ] `docker compose ps` mostra todos os serviços `(healthy)`

  - [ ] Enviar mensagem de teste via Evolution API → bot responde em ≤10s

  - [ ] Fluxo completo de agendamento executado sem erro (verificar disponibilidade → coletar dados → confirmar)

  - [ ] Transbordo humano: bot pausa, admin notificado, bot retoma após expiração

  - [ ] Mensagem de grupo ignorada corretamente



### [TASK-DEP-5.2] Criar `docker-compose.prod.yml` com Overrides de Produção

- **Regra:** Ambiente de produção não deve ter bind-mounts de código-fonte.

- **Critérios de Aceite:**

  - [ ] `docker-compose.prod.yml` remove `volumes: - ./app:/app/app` e `- ./mcp_servers:/app/mcp_servers`

  - [ ] Imagens buildadas com `docker compose -f docker-compose.yml -f docker-compose.prod.yml build`

  - [ ] Variáveis de ambiente lidas de `.env` externo (não commitado)

  - [ ] Validação: `docker compose -f docker-compose.prod.yml up` funciona sem código no host


