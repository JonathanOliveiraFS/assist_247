---
name: integra-reviewer
description: Expert code reviewer for Integra.ai (Multi-tenancy, MCP, RAG). Focuses on security isolation, contract compliance, and retrieval precision. Use when reviewing pull requests, verifying new integrations, or auditing current architecture.
---

# Integra Reviewer

## Overview
This skill acts as a senior technical reviewer for the **Integra.ai** project. It enforces strict security (multi-tenancy), interoperability (MCP), and quality (RAG) standards.

## Review Pillars

### 1. Multi-tenancy Security (Customer Isolation)
The absolute priority is preventing data leakage between clients.
- **Reference Checklist:** [multi_tenancy_checklist.md](references/multi_tenancy_checklist.md)
- **Key Check:** Ensure `customer_id` is propagated from the webhook to the RAG retrievers and MCP tool-calls.

### 2. MCP Contract Compliance
Verify that all tool integrations follow the Model Context Protocol.
- **Reference Checklist:** [mcp_compliance.md](references/mcp_compliance.md)
- **Key Check:** Check that tool schemas are semantic and that client/server handshakes are robust.

### 3. RAG Precision & Synthesis Quality
Audit the retrieval-augmented generation pipeline.
- **Reference Checklist:** [rag_precision.md](references/rag_precision.md)
- **Key Check:** Review chunking logic in Kestra pipelines and `EnsembleRetriever` weights in the agent.

### 4. Architectural Guardrails
Ensure code aligns with the macro-architecture defined in `@GEMINI.MD`.
- **Motor de Tempo Real:** Keep it lean (FastAPI + Redis).
- **Motor de Backoffice:** ETL should stay in Kestra.
- **Human-in-the-Loop:** State must be consistent in Redis.

## How to Review
1.  **Read the Diff:** Focus on data flow involving `customer_id`.
2.  **Run Checklists:** Apply relevant checklists from `references/`.
3.  **Provide Feedback:** Categorize issues as **[CRITICAL]** (Security/Isolation), **[CONTRACT]** (MCP errors), or **[PRECISION]** (RAG improvements).

## Resources

### references/
- **[multi_tenancy_checklist.md](references/multi_tenancy_checklist.md):** Security and isolation checks.
- **[mcp_compliance.md](references/mcp_compliance.md):** Protocol standards.
- **[rag_precision.md](references/rag_precision.md):** Retrieval quality audit.
