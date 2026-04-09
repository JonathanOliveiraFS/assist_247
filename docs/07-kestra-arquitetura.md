# Arquitetura Kestra 1.3+ para Integra.ai (SaaS)

Este documento detalha a integração do Kestra como o "Sistema Nervoso Central" do Integra.ai, focando em operações assíncronas, monitoramento e inteligência de backoffice.

## 1. Gestão de Documentos e Dados (RAG)

### Estratégia de Armazenamento: Shared Docker Volume
Para garantir a consistência dos dados entre o orquestrador (Kestra) e o motor de tempo real (FastAPI/Bot), utilizaremos um **Docker Volume compartilhado** (bind mount no ambiente atual).

- **Diretório:** `rag_data/`
- **Subdiretórios:**
  - `docs/{tenant_id}/`: PDFs e documentos brutos.
  - `chromadb/`: Banco vetorial compartilhado.
  - `bm25_indexes/`: Índices léxicos `.pkl` por tenant.

**Justificativa:** Embora o Kestra 1.3 possua o recurso de *Assets*, ele é mais adequado para artefatos internos de fluxos. O RAG exige persistência de longo prazo e acesso de baixa latência por ambos os containers. O volume compartilhado evita duplicação de dados e simplifica a atualização dos índices.

## 2. Orquestração de Fluxos (.yaml)

Os fluxos serão organizados no namespace `io.integra.ai` e utilizarão plugins modernos da versão 1.x.

### Fluxos Mapeados:
1. `rag_sync.yaml`: Disparado via Webhook ou Schedule. Executa scripts de chunking e indexação.
2. `health_monitor.yaml`: Disparado a cada 5 minutos. Valida conectividade de serviços.
3. `b2b_reports.yaml`: Disparado semanalmente (Cron). Consolida dados no Notion/Airtable.
4. `finops_tokens.yaml`: Disparado diariamente. Processa logs de uso da OpenAI.
5. `crm_proactive.yaml`: Disparado via consulta ao Notion. Inicia conversas via API do Bot.

### Uso de Plugins:
- **Python Tasks:** `io.kestra.plugin.scripts.python.Commands` rodando em containers isolados (Docker Task Runner).
- **Notificações:** `io.kestra.plugin.notifications` para alertas críticos.

## 3. Invocação de Scripts e Multi-tenancy

O `tenant_id` será tratado como uma variável de contexto mandatória em todos os fluxos que operam sobre dados de clientes.

### Exemplo de Task Runner (Kestra 1.3):
```yaml
tasks:
  - id: build_index
    type: io.kestra.plugin.scripts.python.Commands
    runner: DOCKER
    docker:
      image: python:3.11-slim
    env:
      TENANT_ID: "{{ inputs.tenant_id }}"
      OPENAI_API_KEY: "{{ secret.OPENAI_API_KEY }}"
    commands:
      - pip install -r scripts/requirements_rag.txt
      - python scripts/build_bm25.py --tenant $TENANT_ID
```

## 4. Comunicação Docker Network

O Kestra acessará os outros serviços via rede interna do Docker Compose:
- **Bot FastAPI:** `http://integra_ai_bot:8000`
- **Evolution API:** `http://evolution_api_integra:8080`
- **Redis:** `redis_integra:6379`

## 5. Segurança e Governança
- **Secrets:** Uso do gerenciador de segredos do Kestra para `OPENAI_API_KEY` e chaves de banco.
- **Isolamento:** Cada execução de script Python ocorre em um container efêmero, garantindo que dependências de um tenant não afetem outros.
