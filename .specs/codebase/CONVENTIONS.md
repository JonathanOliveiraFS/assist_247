# Convenções do Projeto

## Código Python
- **Padrão:** PEP8.
- **Tipagem:** Uso obrigatório de `Type Hints`.
- **Validação:** Pydantic para modelos de dados e configurações (`pydantic-settings`).
- **Assincronismo:** Preferência por `async/await` em todas as rotas de IO (FastAPI, Redis, EvolutionAPI).

## Organização de Arquivos
- `app/`: Lógica central do chatbot.
- `mcp_servers/`: Servidores de ferramentas isolados por funcionalidade.
- `kestra/`: Definições de fluxos YAML.

## Nomenclatura
- Classes: `PascalCase`.
- Funções/Variáveis: `snake_case`.
- Variáveis de Ambiente: `UPPER_SNAKE_CASE`.

## Commits
- Seguir o padrão de **Conventional Commits** (feat, fix, docs, refactor).
- Commits atômicos (uma mudança lógica por commit).

## Gestão de Ambiente
- Todas as variáveis críticas devem estar no `.env` e mapeadas no `app/config.py`.
