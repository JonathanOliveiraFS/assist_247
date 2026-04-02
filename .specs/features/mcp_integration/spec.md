# Spec: Integração com MCP para Tool Calling (Fase 5)

O objetivo desta funcionalidade é permitir que o bot Integra.ai execute ações externas (ferramentas) via Model Context Protocol (MCP). Como prova de conceito (PoC), implementaremos um servidor MCP local que fornece uma ferramenta de agendamento, permitindo que o LLM realize marcações de reuniões de forma estruturada.

## Requisitos Funcionais
1. **Tool Calling Nativo:** O bot deve ser capaz de identificar quando o usuário deseja realizar um agendamento e invocar a ferramenta apropriada.
2. **Servidor MCP Mock:** Criar um servidor MCP isolado que simula a lógica de negócio de agendamento.
3. **Ferramenta `agendar_reuniao`:**
   - **Inputs:** `data_hora` (string, ex: "2024-05-10 14:00").
   - **Outputs:** Mensagem de confirmação simulada (ex: "Agendamento realizado com sucesso para [data_hora].").
4. **Integração com LangChain:** O `bot_agent.py` deve carregar dinamicamente as ferramentas do servidor MCP e vinculá-las ao modelo `gpt-4o-mini` usando `bind_tools`.

## Requisitos Técnicos
1. **Servidor MCP (`mcp_servers/mcp_mock/server.py`):**
   - Utilizar a biblioteca `mcp` (SDK oficial).
   - Definir a ferramenta `agendar_reuniao` com esquema JSON Schema para os argumentos.
   - Expor o servidor via `stdio` para comunicação local com o processo do bot.
2. **Módulo `app/bot_agent.py`:**
   - Integrar `langchain-mcp-adapters` para converter ferramentas MCP em ferramentas LangChain (`BaseTool`).
   - Implementar a inicialização do cliente MCP (Stdio transport).
   - Atualizar a lógica de `process_chat` para suportar o fluxo de "Reasoning and Acting" (ReAct ou chamadas de ferramentas sequenciais).
3. **Gerenciamento de Dependências:**
   - Adicionar `langchain-mcp-adapters` ao `pyproject.toml`.
4. **Isolamento (Dockerfile):**
   - Preparar um `Dockerfile` simples para o `mcp_mock` para manter a consistência com a arquitetura do projeto.

## Fluxo de Dados
1. O usuário envia: "Quero agendar uma reunião para amanhã às 15h".
2. O `bot_agent` processa a mensagem e recupera contexto do RAG (se houver).
3. O LLM identifica a intenção de agendamento e emite uma `tool_call` para `agendar_reuniao`.
4. O `bot_agent` intercepta a chamada, executa via MCP Client no servidor `mcp_mock`.
5. O servidor retorna: "Sucesso: Agendado para 2026-04-03 15:00".
6. O LLM recebe o resultado da ferramenta e gera a resposta final amigável para o WhatsApp.

## Traceability
- **ID:** FEAT-MCP-001
- **Status:** Planning
- **Roadmap:** Fase 5
- **Dependencies:** Fase 4 (RAG)
