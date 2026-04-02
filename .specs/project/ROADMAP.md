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

## Fase 4: Inteligência & Conhecimento (RAG) [EM DEFINIÇÃO]
- [ ] Implementação do `app/rag_service.py` (ChromaDB)
- [ ] Persistência vetorial em `rag_data/chromadb`
- [ ] Injeção de contexto no `app/bot_agent.py`
- [ ] Busca Híbrida (Ensemble: Chroma + BM25)

## Fase 5: Ferramentas & MCP [PLANEJADO]
- [ ] Implementação de Clientes MCP no Agente
- [ ] Integração com `mcp_agenda_clinica`
- [ ] Integração com `mcp_crm_integra`

## Fase 6: Human-in-the-Loop & Transbordo [PLANEJADO]
- [ ] Detecção de intenção de transbordo (IA -> Humano)
- [ ] Gerenciamento de estado de atendimento no Redis
- [ ] Dashboard administrativo simples para transbordo

## Fase 7: Backoffice & Pipelines (Kestra) [PLANEJADO]
- [ ] Pipeline de ingestão automática de documentos
- [ ] Invalidação de cache e recarga de índices RAG
