# Fluxos de Processamento - Integra.ai

Este documento descreve os fluxos operacionais e arquiteturais do sistema.

## 1. Fluxo de RAG Dinâmico & Auto-Build

================================================================================
 FASE 1: SETUP ADMINISTRATIVO (Ação Humana Rápida - 2 minutos)
================================================================================
 
 1. 🤝 Cliente Assina -> Nova empresa entra (ex: "Odonto Clean").
 2. 📱 Evolution API -> Você cria a instância "odonto_clean" e lê o QR Code.
 3. 📁 Pastas Locais -> Você cria a pasta: /rag_data/docs/odonto_clean/
 4. 📄 Upload Docs   -> Você arrasta o arquivo "tabela_precos.pdf" e "regras.docx" 
                        para dentro desta nova pasta.
 5. ✅ Trabalho Humano Encerrado. O sistema está aguardando.

================================================================================
 FASE 2: GATILHO & AUTO-BUILD (Ação da Máquina - 1ª Mensagem do Cliente)
================================================================================

 [WhatsApp] 👤 Cliente final manda a primeira mensagem: "Quanto custa o clareamento?"
       │
       ▼
 [Webhook] 🌐 Evolution API dispara o evento para o FastAPI.
              (Instância detectada: tenant_id = "odonto_clean")
       │
       ▼
 [Bot Agent] 🤖 A IA pede ajuda ao RAG Service para ter contexto.
       │
       ▼
 [RAG Service] 🧠 Procura o índice "odonto_clean_index.pkl".
       │
       ├─► [Cenário A: Já Existe] 🟢 -> Faz a busca em milissegundos e responde.
       │
       └─► [Cenário B: NÃO Existe (É a 1ª mensagem!)] 🟡 -> ATIVA O AUTO-BUILD:
                 │
                 ├─ 1. Lê a pasta /docs/odonto_clean/
                 ├─ 2. Usa PyPDFLoader (.pdf) e DocxLoader (.docx)
                 ├─ 3. Fatiamento (Chunking) do texto.
                 ├─ 4. Salva os Vetores (ChromaDB) silenciosamente.
                 ├─ 5. Salva o Arquivo Léxico (BM25 .pkl) silenciosamente.
                 │
                 ▼
 [Busca Concluída] 🟢 Agora o índice existe! O RAG faz a busca na mesma hora.
       │
       ▼
 [LLM OpenAI] 💬 Gera a resposta perfeita com base nos preços do PDF.
       │
       ▼
 [WhatsApp] 👤 Cliente recebe a resposta: "Olá! O clareamento custa..."

================================================================================
 FASE 3: OPERAÇÃO DE CRUZEIRO (Ação Contínua)
================================================================================

 A partir da segunda mensagem em diante, o Cenário B nunca mais acontece. 
 O sistema já tem o `.pkl` da "Odonto Clean" salvo e passa a responder 
 todas as mensagens em milissegundos usando o Cenário A.

## Requisitos Técnicos Globais
- Uso de `AsyncExitStack` no `mcp_manager.py` para gerenciamento de ciclo de vida de ferramentas.
- Persona BIA: Respostas amigáveis, sem termos técnicos.
