🤖 Integra.ai - Chatbot IA Corporativo para WhatsApp (Arquitetura B2B)
📋 Características do Projeto
Funcionalidades Principais
Integração WhatsApp: Conecta via EvolutionAPI para enviar e receber mensagens.

Transbordo Estratégico (Human-in-the-Loop): Sistema de pausa da IA para assumir o atendimento humano quando necessário.

RAG Híbrido de Alta Precisão: Combina busca semântica (ChromaDB) com busca léxica/palavras-chave (BM25) para máxima exatidão em matrizes de clínicas e clientes.

Multi-tenancy Isolado: Separação rigorosa de dados (Vector Store e Histórico) por cliente/empresa.

Arquitetura Baseada em MCP (Model Context Protocol): Integração com sistemas externos (agendas, CRMs) via servidores MCP isolados, substituindo funções locais por contratos padronizados.

Orquestração de Dados (Backoffice): Pipelines automatizados via Kestra para atualização contínua e assíncrona das bases de conhecimento.

Buffer de Mensagens: Agrupa mensagens fragmentadas do WhatsApp com sistema de debounce via Redis.

Tecnologias Utilizadas
FastAPI: Framework web de alta performance para a API em tempo real.

Kestra: Orquestrador de fluxos de dados e ETL (atualização do RAG).

LangChain & LangChain MCP: Orquestração de chains de IA e cliente de ferramentas.

OpenAI API: Modelos de linguagem fundacionais.

Redis: Cache, buffer de mensagens, histórico de conversas e status de atendimento (Bot vs Humano).

ChromaDB & BM25: Vector store (semântico) e índice léxico para o RAG Híbrido.

Docker / Docker Compose: Containerização completa e isolamento de serviços/MCPs.

🏗️ Stack Técnico e Arquitetura Macro
O sistema é dividido em dois "motores" principais para garantir baixa latência no WhatsApp e alta capacidade de processamento em background:
┌─────────────────────────────────────────────────────────────┐
│                   MOTOR DE TEMPO REAL                       │
│                                                             │
│  ┌────────────┐   ┌────────────┐   ┌─────────────────────┐  │
│  │ WhatsApp   ├───► FastAPI    ├───► Redis (Buffer/      │  │
│  │ (Evolution)│   │ (Webhook)  │   │        Status/Mem)  │  │
│  └────────────┘   └──────┬─────┘   └─────────────────────┘  │
│                          │                                  │
│                   ┌──────▼─────┐   ┌─────────────────────┐  │
│                   │ LangChain  ├───► Servidores MCP      │  │
│                   │ (Agente)   │   │ (Agenda, CRM, etc.) │  │
│                   └──────┬─────┘   └─────────────────────┘  │
│                          │                                  │
│                   ┌──────▼─────┐                            │
│                   │ OpenAI LLM │                            │
│                   └────────────┘                            │
└─────────────────────────────────────────────────────────────┘
                               ▲
┌──────────────────────────────┼──────────────────────────────┐
│                  MOTOR DE BACKOFFICE (DADOS)                │
│                              │                              │
│  ┌────────────┐   ┌──────────┴─┐   ┌─────────────────────┐  │
│  │ Docs/S3/   ├───► Kestra     ├───► RAG Híbrido         │  │
│  │ Drive      │   │ (Pipelines)│   │ (Chroma + BM25)     │  │
│  └────────────┘   └────────────┘   └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
🔄 Fluxogramas de Processamento
1. Fluxo de Atendimento em Tempo Real (FastAPI)
graph TD
    A["📱 Mensagem WhatsApp"] --> B["🔗 Webhook FastAPI"]
    B --> C{"Status no Redis<br/>é 'Humano'?"}
    C -->|Sim| D["⏸️ Ignora (Atendente Assumiu)"]
    C -->|Não| E{"Mensagem Própria/Grupo?"}
    E -->|Sim| D
    E -->|Não| F["📦 Redis Buffer<br/>Inicia Debounce"]
    F --> G{"Mais mensagens<br/>no tempo?"}
    G -->|Sim| F
    G -->|Não| H["🔀 Agrupa Mensagens"]
    H --> I["🤖 LangChain Agent"]
    I --> J{"Requer Ferramenta /<br/>Consulta Base?"}
    J -->|Base de Dados| K["🔍 RAG Híbrido<br/>Chroma (Semântica) + BM25 (Exata)"]
    J -->|Ação Externa| L["🔌 Cliente MCP<br/>Consulta Servidor MCP (Docker)"]
    K --> M["🧠 LLM OpenAI"]
    L --> M
    M --> N["📤 EvolutionAPI<br/>Envia Resposta"]
    N --> O["✅ Fim"]

2. Fluxo de Atualização de Conhecimento (Kestra)
graph TD
    A["📄 Cliente atualiza<br/>Matriz/Documento"] --> B["⚡ Trigger Kestra"]
    B --> C["📥 Download do Documento"]
    C --> D["✂️ Text Splitter<br/>(Chunking)"]
    D --> E["🧮 Gera Embeddings<br/>(OpenAI)"]
    E --> F["💾 Atualiza ChromaDB<br/>(Collection do Cliente)"]
    D --> G["🔤 Tokenização<br/>BM25"]
    G --> H["💾 Salva Pickle BM25<br/>(Índice do Cliente)"]
    F --> I["🔔 Webhook Notifica API<br/>para recarregar memória"]
    H --> I

📁 Estrutura de Arquivos Modular (Clean Architecture)
integra_ai_bot/
├── app/
│   ├── core/                   # Configurações, Redis, MCP Manager, Tenants
│   ├── services/               # Lógica do Agente, RAG, Evolution Service
│   ├── models/                 # Modelos de dados e Schemas Pydantic
│   └── main.py                 # Ponto de entrada FastAPI e Lifespan
├── kestra/                     # Fluxos de orquestração (antigo kestra_flows)
├── mcp_servers/                # Servidores MCP isolados (Agenda, CRM, etc.)
├── rag_data/                   # Dados persistentes (ChromaDB, BM25 Index)
├── tests/                      # Testes automatizados e setups de teste
├── scripts/                    # Utilitários de build, setup e manutenção
├── docs/                       # Documentação, Pesquisas e Referências de Skills
├── docker-compose.yml          # Orquestração de containers
├── Dockerfile                  # Build da imagem da API
└── pyproject.toml              # Gerenciamento de dependências (UV)

🔑 Componentes Principais Detalhados
1. Human-in-the-Loop (Transbordo)
Sistema crítico de segurança. O estado da conversa (bot ou human) fica armazenado no Redis. O LLM é instruído (via prompt) a alterar esse status caso detecte frustração ou intenção direta de falar com um atendente. Enquanto o status for human, o webhook descarta silenciosamente as mensagens, permitindo que a equipe de atendimento opere o chat.

2. RAG Híbrido Segmentado (Multi-tenancy)
Para evitar vazamento de dados entre clientes:

Busca Semântica: O ChromaDB utiliza Collections isoladas pelo ID do cliente (ex: collection_name="cliente_xyz"), garantindo que a IA entenda o contexto sem misturar bases.

Busca Léxica (BM25): Garante precisão absoluta em jargões médicos, códigos de procedimentos e políticas de filiais. Um arquivo .pkl separado é mantido para cada cliente.

Ensemble Retriever: O LangChain une e re-ranqueia os resultados de ambas as buscas.

3. Integração MCP (Model Context Protocol)
Em vez de funções hardcoded (Tools), a aplicação atua como um MCP Client. As integrações com sistemas legados, ERPs ou agendas de clínicas rodam em containers Docker independentes (MCP Servers). Isso garante:

Segurança: Credenciais do cliente não ficam no código principal.

Escalabilidade: Novos clientes recebem novos containers MCP sem alterar o bot base.

4. Pipelines Kestra
Remove a carga de ETL (Extract, Transform, Load) do bot principal. O Kestra processa arquivos massivos em background, atualiza os bancos vetoriais e léxicos, e notifica o FastAPI apenas quando os dados estão prontos para consumo.

🔐 Variáveis de Configuração Essenciais
Variável                     Descrição      
OPENAI_API_KEY               Autenticação OpenAI (LLM e Embeddings)
EVOLUTION_API_URL / API_KEY  Credenciais do EvolutionAPI
REDIS_URL                    Conexão para Buffer, Memória e controle de Transbordo
CHROMA_PERSIST_DIR           Volume persistente do banco vetorial
BM25_INDEX_DIR               Diretório dos modelos léxicos (.pkl)KESTRA_API_URL               Comunicação com o Kestra (opcional via webhook)MCP_SERVERS_CONFIG           Mapeamento dinâmico das URLs dos servidores MCP


