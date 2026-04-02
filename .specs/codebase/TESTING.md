# Estratégia de Testes

## Estado Atual
- **Identificado:** Atualmente o projeto não possui uma suíte de testes formal configurada no `pyproject.toml`.
- **Risco:** Falta de validação automática para mudanças no RAG e no comportamento do Agente.

## Plano de Implementação
- **Framework:** Pytest.
- **Tipos de Teste:**
  - **Unitários:** Testar o `redis_manager` (debounce) e o `evolution_service`.
  - **Integração:** Mockar o EvolutionAPI e testar o fluxo de Webhook -> Agente -> Resposta.
  - **Evals de IA:** Utilizar `LangSmith` ou frameworks similares para testar a qualidade das respostas do RAG Híbrido.

## Comandos Recomendados (Futuro)
- `pytest`: Executar suite completa.
- `pytest --cov=app`: Verificar cobertura de testes.
