# Spec: Integração do RAG com ChromaDB (Fase 4)

O objetivo desta funcionalidade é permitir que o bot consulte uma base de conhecimento persistente para responder de forma fundamentada aos usuários. Inicialmente, focaremos na busca semântica utilizando ChromaDB e OpenAI Embeddings.

## Requisitos Funcionais
1. **Persistência de Dados:** O banco vetorial deve ser salvo no diretório `rag_data/chromadb`.
2. **Isolamento por Cliente (Multi-tenancy):** As buscas devem ser filtradas ou direcionadas para coleções específicas baseadas no `tenant_id` (ID da instância do WhatsApp).
3. **Busca Semântica:** Implementar recuperação de documentos relevantes baseada em similaridade de cosseno via OpenAI Embeddings.
4. **Contextualização do LLM:** Injetar os fragmentos recuperados no prompt do Agente LangChain.

## Requisitos Técnicos
1. **Módulo `app/rag_service.py`:**
   - Classe `RAGService` para gerenciar conexões com ChromaDB.
   - Método `get_relevant_documents(query, tenant_id)` para busca.
2. **Atualização `app/bot_agent.py`:**
   - Integrar o `RAGService` na função `process_chat`.
   - Modificar o prompt do sistema para incluir o bloco `{context}`.
3. **Configuração:**
   - Garantir que as variáveis `CHROMA_PERSIST_DIR` e `OPENAI_API_KEY` estejam sendo lidas corretamente.

## Fluxo de Dados
1. Mensagem chega via Webhook.
2. Debounce agrupa mensagens.
3. `bot_agent` chama `rag_service` com a query agrupada.
4. `rag_service` consulta a coleção do `tenant_id` no ChromaDB.
5. `bot_agent` monta prompt: `Contexto: [Documentos] | Pergunta: [Query]`.
6. LLM gera resposta.
7. Resposta é enviada via EvolutionAPI.

## Traceability
- **ID:** FEAT-RAG-001
- **Status:** Planning
- **Roadmap:** Fase 4
