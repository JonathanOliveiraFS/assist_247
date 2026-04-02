# Integra.ai - Plataforma de Atendimento Corporativo IA

Plataforma robusta de atendimento B2B via WhatsApp que utiliza Inteligência Artificial avançada, RAG Híbrido (Busca Semântica + Léxica) e automação de fluxos de trabalho (Kestra e Model Context Protocol - MCP).

## Visão do Projeto
Criar um ecossistema de atendimento inteligente onde a IA não apenas conversa, mas resolve problemas complexos integrando-se a sistemas legados (agendas, CRMs) e mantendo uma base de conhecimento técnica e atualizada por cliente (Multi-tenancy).

## Objetivos Principais
- **Precisão Técnica:** RAG Híbrido (ChromaDB + BM25) para evitar alucinações em dados sensíveis.
- **Isolamento de Dados:** Arquitetura Multi-tenant rigorosa para separação de clientes/clínicas.
- **Automação Escalável:** Uso de MCP para ferramentas externas e Kestra para pipelines de dados.
- **Experiência Fluida:** Sistema de debounce para mensagens fragmentadas no WhatsApp.

## Stack Tecnológica
- **Backend:** FastAPI (Python 3.11+)
- **IA/Orquestração:** LangChain, LangGraph, OpenAI (GPT-4o/Embeddings)
- **Banco Vetorial:** ChromaDB
- **Busca Léxica:** BM25 (Rank-BM25)
- **Mensageria/Gateway:** EvolutionAPI (WhatsApp)
- **Cache/Estado:** Redis
- **Data Ops:** Kestra
- **Protocolo de Ferramentas:** Model Context Protocol (MCP)
