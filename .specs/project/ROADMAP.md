# Roadmap do Projeto - Integra.ai

## Fase 1: Fundação & Infraestrutura [CONCLUÍDO]
- [x] Configuração do ambiente (uv, Docker, Docker Compose)
- [x] Estrutura base do FastAPI
- [x] Configuração do Redis para Buffer

## Fase 2: Gateway de Mensageria (EvolutionAPI) [CONCLUÍDO]
- [x] Webhook para recepção de mensagens
- [x] Serviço de envio de mensagens de texto
- [x] Lógica de Debounce via Redis

## Fase 3: Orquestração Base (LangChain) [CONCLUÍDO]
- [x] Integração com OpenAI (GPT-4o-mini)
- [x] Agrupamento de mensagens do buffer para o LLM
- [x] Fluxo básico de Resposta Automática

## Fase 4: Inteligência & Conhecimento (RAG) [CONCLUÍDO]
- [x] Implementação do `app/rag_service.py` (ChromaDB)
- [x] Persistência vetorial em `rag_data/chromadb`
- [x] Injeção de contexto no `app/bot_agent.py`
- [x] Busca Híbrida (Ensemble: Chroma + BM25)

## Fase 5: Ferramentas & MCP [CONCLUÍDO]
- [x] Implementação de Clientes MCP no Agente (`app/bot_agent.py`)
- [x] Integração com Airtable (Agendamentos)
- [x] Integração com Notion (CRM baseado no template Centralize)

## Fase 6: Human-in-the-Loop & Transbordo [CONCLUÍDO]
- [x] Detecção de intenção de transbordo (IA -> Humano)
- [x] Gerenciamento de estado de atendimento no Redis (Pausa de 24h)
- [x] Sistema de notificação instantânea para o Administrador via Evolution API

## Fase 7: Backoffice & Pipelines (Kestra) [PRÓXIMO PASSO]
- [ ] Orquestração de tarefas de manutenção do RAG
- [ ] Monitoramento de saúde dos servidores e APIs
- [ ] Automação de relatórios semanais de leads
