# Integra.ai - State Management

## Sessão Atual: 2026-04-02
### Decisões
- **[RAG-01] Persistência:** Utilizar o diretório `rag_data/chromadb` como `persist_directory`. (EXECUTADO)
- **[RAG-01] Multi-tenancy:** Implementar o isolamento por `tenant_id` utilizando coleções separadas no ChromaDB (padrão: `cliente_{tenant_id}`). (EXECUTADO)
- **[RAG-01] Embeddings:** Utilizar `text-embedding-3-small` da OpenAI por ser mais eficiente e econômico. (EXECUTADO)
- **[RAG-01] Biblioteca:** Migrar de `langchain-community` (Chroma) para o pacote dedicado `langchain-chroma`. (EXECUTADO)


### Bloqueios
- Nenhum no momento.

### Ideias Diferidas
- Implementar busca híbrida (BM25) em uma sub-tarefa posterior para não aumentar a complexidade inicial.
- Cache de retrievers no `RAGService` para evitar re-instanciação frequente.
