# Integrações Externas

## 1. EvolutionAPI
- **Função:** Gateway para o WhatsApp.
- **Fluxo de Entrada:** Recebe webhooks de mensagens e estados de presença.
- **Fluxo de Saída:** Envia mensagens de texto, áudio e mídia via API REST.
- **Autenticação:** API Key fixa via cabeçalho `apikey`.

## 2. Redis
- **Buffer de Mensagens:** Implementa debounce de 2-3 segundos para agrupar mensagens fragmentadas do usuário (ex: "Oi", "Tudo bem?", "Quero marcar").
- **Human-in-the-Loop:** Armazena uma flag `tenant:{id}:chat:{phone}:status = 'human'` para pausar o bot.

## 3. MCP (Model Context Protocol)
- **Implementação:** O bot atua como `MCP Client` utilizando `langchain-mcp-adapters`.
- **Conexão:** Via transporte `stdio` configurado com `StdioServerParameters`.
- **Orquestração:** Utiliza `langgraph.prebuilt.create_react_agent` para gerenciar o ciclo de vida de chamadas de ferramentas (Tool Calling).
- **Servidores:** 
  - `mcp_mock`: Servidor PoC em Python (FastMCP) que fornece a ferramenta `agendar_reuniao`.
- **Dinâmica:** O LLM analisa a entrada do usuário e o contexto do RAG. Se necessário, emite uma `tool_call` que é executada pelo cliente MCP antes da resposta final.

## 4. Kestra
- **Trigger:** Webhooks ou monitoramento de diretórios/S3.
- **Saída:** Escreve arquivos na pasta `rag_data/` que são montados como volumes no container da API.
