# Tasks: Integração com MCP para Tool Calling (Fase 5)

Este documento detalha as tarefas necessárias para implementar a Prova de Conceito (PoC) de integração com servidores MCP.

## 1. Preparação do Ambiente e Dependências
- [x] Adicionar `langchain-mcp-adapters` ao `pyproject.toml`.
- [x] Executar `uv sync` ou `pip install` para atualizar o ambiente virtual.

## 2. Desenvolvimento do Servidor MCP Mock
- [x] Criar o diretório `mcp_servers/mcp_mock/`.
- [x] Criar `mcp_servers/mcp_mock/server.py`:
  - [x] Implementar servidor básico usando `mcp.Server`.
  - [x] Definir a ferramenta `agendar_reuniao(data_hora: str)`.
  - [x] Adicionar logica de retorno simulado de sucesso.
- [x] Criar `mcp_servers/mcp_mock/Dockerfile` baseado em `python:3.11-slim`. (Nota: Pulado conforme orientação do usuário para uso via stdio local)

## 3. Integração no Bot Agent (`app/bot_agent.py`)
- [x] Implementar função auxiliar `get_mcp_tools()`: (Nota: Incorporado diretamente no fluxo `async with`)
  - [x] Configurar `StdioServerParameters` para o processo `python mcp_servers/mcp_mock/server.py`.
  - [x] Utilizar `load_mcp_tools` do `langchain-mcp-adapters` para importar as ferramentas.
- [x] Refatorar `process_chat`:
  - [x] Instanciar o LLM e realizar o `bind_tools`.
  - [x] Substituir `ainvoke` simples por um loop de execução de ferramentas ou `AgentExecutor`.
  - [x] Garantir que o contexto do RAG continue sendo injetado no prompt do sistema.

## 4. Validação e Testes
- [x] Criar script `test_mcp_integration.py` para validar o fluxo fim-a-fim: (Nota: Validado via integração manual conforme acordado)
- [x] Verificar logs de erro para garantir que a conexão `stdio` entre processos é encerrada corretamente após o uso.

## 5. Documentação Final
- [x] Atualizar `.specs/codebase/INTEGRATIONS.md` com os detalhes da implementação do MCP Client.
- [x] Atualizar o status da Phase 5 no Roadmap global.
