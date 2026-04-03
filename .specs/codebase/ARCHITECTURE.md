# Arquitetura Macro - Integra.ai

O sistema é dividido em dois motores principais para garantir baixa latência no WhatsApp e processamento pesado em background.

## 1. Motor de Tempo Real (Real-time Engine)
Processa as mensagens que chegam do WhatsApp via EvolutionAPI.

- **FastAPI Webhook:** Recebe o JSON da mensagem.
- **Redis Manager:** 
  - Verifica status `human-in-the-loop` (se ativo, o bot silencia).
  - Realiza **Debounce** (agrupa mensagens fragmentadas enviadas em sequência pelo usuário).
- **LangChain Agent:** 
  - Recebe o texto agrupado.
  - Utiliza `create_agent` da biblioteca `langchain.agents` (Padrão LangChain v1.0).
  - Recebe o `system_prompt` (com contexto RAG) diretamente como parâmetro.
  - Decide se precisa consultar a base de conhecimento (RAG) ou executar uma ferramenta (MCP).
- **EvolutionAPI Wrapper:** Envia a resposta final para o usuário.

## 2. Motor de Dados (Backoffice Engine)
Responsável por manter a inteligência do bot atualizada.

- **Kestra Pipelines:** 
  - Monitora atualizações de documentos (PDF, Docx, etc.).
  - Processa chunking e gera embeddings.
  - Atualiza o ChromaDB (vetores) e os índices BM25 (léxico) de forma isolada por cliente.
  - Notifica a API principal para invalidar caches de memória de contexto.

## Multi-tenancy
- **Isolamento de Dados:** Cada cliente possui sua própria `collection` no ChromaDB e seu próprio arquivo `.pkl` para busca léxica.
- **Isolamento de Ferramentas:** Servidores MCP rodam em containers separados ou processos isolados. Na Fase 5, o servidor `mcp_mock` está localizado em `mcp_servers/mcp_mock/server.py` e é executado via transporte `stdio`.
