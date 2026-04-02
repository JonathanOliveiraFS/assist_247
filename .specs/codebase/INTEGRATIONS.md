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
- **Implementação:** O bot atua como `MCP Client`.
- **Conexão:** Via Stdio ou HTTP com os containers em `mcp_servers/`.
- **Dinâmica:** Permite que o LLM execute funções externas sem que o código principal precise conhecer os detalhes da implementação da ferramenta.

## 4. Kestra
- **Trigger:** Webhooks ou monitoramento de diretórios/S3.
- **Saída:** Escreve arquivos na pasta `rag_data/` que são montados como volumes no container da API.
