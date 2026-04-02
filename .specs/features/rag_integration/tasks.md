# Tarefas: Integração do RAG com ChromaDB

## [RAG-01] Implementação do RAGService
- [x] Criar arquivo `app/rag_service.py`.
- [x] Implementar inicialização do cliente ChromaDB usando `settings.chroma_persist_dir`.
- [x] Configurar `OpenAIEmbeddings` com a API Key do projeto.
- [x] Criar método `get_retriever(tenant_id)` que retorna um LangChain Retriever para a coleção específica do cliente.
- **Critério de Aceite:** O serviço deve conseguir instanciar o ChromaDB sem erros e retornar um objeto retriever válido. (CONCLUÍDO)

## [RAG-02] Atualização do Bot Agent
- [x] Importar `RAGService` em `app/bot_agent.py`.
- [x] Atualizar a função `process_chat` para aceitar um parâmetro opcional `tenant_id`.
- [x] Implementar a chamada ao retriever antes de invocar o LLM.
- [x] Formatar o contexto recuperado (docs) em uma string única.
- [x] Atualizar o prompt do `SystemMessage` para instruir o bot a usar o contexto fornecido.
- **Critério de Aceite:** O log deve mostrar documentos sendo recuperados (se existirem) e o LLM deve receber esses documentos no prompt. (CONCLUÍDO)

## [RAG-03] Integração no Webhook (main.py)
- [x] Atualizar a rota `/webhook` e a tarefa de background `process_debounced_messages` para extrair o `tenant_id` (usando `payload.instance`).
- [x] Passar o `tenant_id` para a chamada de `process_chat`.
- **Critério de Aceite:** O fluxo completo deve funcionar desde a chegada da mensagem até a geração da resposta contextualizada. (CONCLUÍDO)

## [RAG-04] Validação & Teste de Persistência
- [ ] Criar um script temporário `test_rag_setup.py` para inserir um documento de teste no ChromaDB.
- [ ] Verificar se os arquivos são criados em `rag_data/chromadb`.
- [ ] Simular uma pergunta via script e validar se a resposta condiz com o documento inserido.
- **Critério de Aceite:** Persistência confirmada e recuperação funcional.
