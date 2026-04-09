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

## 3. Sprint: Sistema Nervoso Central & Operações (Kestra 1.3+)

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
