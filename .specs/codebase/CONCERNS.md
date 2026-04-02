# Pontos de Atenção & Débitos Técnicos

## 1. Segurança Multi-tenancy
- **Risco:** Como o bot atende múltiplas clínicas, um erro no `redis_manager` ou na query do `ChromaDB` pode vazar informações de um paciente de uma clínica para outra.
- **Ação:** Implementar Middlewares de validação de `tenant_id` em todas as rotas.

## 2. Invalidação de Cache do RAG
- **Problema:** Quando o Kestra atualiza o índice BM25 (arquivo .pkl), a instância da API em execução pode estar com o arquivo antigo em memória.
- **Ação:** Implementar um webhook interno na API (`/admin/reload-index`) para que o Kestra notifique a recarga.

## 3. Sincronismo do Redis Debounce
- **Problema:** Em cenários de alta carga, o lock de debounce pode sofrer race conditions se não for implementado atomicamente com scripts LUA no Redis.

## 4. Cobertura de Testes
- **Problema:** O projeto está crescendo sem testes automatizados, o que torna refatorações do motor de IA perigosas.

## 5. Dependência da EvolutionAPI
- **Problema:** Mudanças na API da Evolution ou instabilidade do container externo param o atendimento. Necessário implementar retentativas exponenciais.
