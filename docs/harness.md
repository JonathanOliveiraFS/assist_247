# Workflow Arquitetural: Agente de WhatsApp com Harness (Integra.ai)

Este documento detalha a implementação da camada de **Harness** (Orquestração) baseada na arquitetura de Ronald Hawk, integrada ao projeto **Assist 24/7**.

## 1. O Conceito de Harness e Externalização
O Harness atua como uma "armadura" ou cinto de segurança para o LLM. Em vez de enviar todo o histórico para o modelo, o Harness gerencia o estado fora do prompt (Externalização), utilizando o **LangGraph** para controlar o fluxo.

## 2. Etapas do Workflow (Passo a Passo)

### Fase A: Ingresso e Recuperação de Estado
1. **Recebimento (Webhook):** A mensagem chega via API do WhatsApp.
2. **Fila de Mensagens:** A mensagem é colocada em uma fila (Redis) para garantir que nenhuma interação seja perdida.
3. **Recuperação de Sessão (Hydration):** O Harness consulta o **Redis/PostgreSQL** usando o número de telefone como chave para recuperar o histórico anterior e o status do cliente.

### Fase B: Ciclo de Orquestração do LangGraph
4. **Nó de Decisão (The Router):** O LLM principal analisa a mensagem + estado recuperado. Ele decide:
    - Se pode responder diretamente.
    - Se precisa de um **Agente Especialista** (Vendas, Suporte).
    - Se precisa de uma **Ferramenta** (Consulta de pedido, RAG).
5. **Execução de Especialista:** Se roteado, o nó do especialista processa a demanda específica e devolve a sugestão ao Harness.

### Fase C: Ações e Memória Externa
6. **RAG & Vector DB:** Se houver dúvida técnica sobre os serviços da Integra, o Harness busca nos documentos técnicos indexados.
7. **Tool Calling (API):** Chamadas para sistemas externos (CRM ou DB) para buscar dados em tempo real.
8. **Checkpointing (Persistência):** Antes de gerar a resposta final, o estado do grafo é salvo. Se o sistema falhar, ele retoma exatamente deste ponto.

### Fase D: Saída e Resposta
9. **Sintetização:** O Harness compila os retornos dos especialistas e ferramentas em uma resposta final coerente.
10. **Egresso:** A resposta é enviada de volta para a fila e disparada para o WhatsApp do usuário.

---

## 3. Especificações Técnicas para Integra.ai
- **Engine:** Python 3.12 + LangGraph.
- **LLM:** atual gpt-4o-mini.
- **Memória:** PostgreSQL (Estado persistente) + Redis (Cache rápido).
- **Conformidade:** Implementação de "Human-in-the-loop" em nós de decisão crítica (Vendas/Fechamento) e solicitação do cliente.