---
name: docs-researcher
description: Exhaustive documentation research and synthesis. Prioritizes MCP Context7 for high-fidelity technical documentation (LangChain, Django, SQL). Use when investigating library capabilities, troubleshooting complex integrations, or generating technical reports with deprecation alerts.
---

# Docs Researcher

## Overview
This skill enables exhaustive documentation research and synthesis for technical projects. It prioritizes high-fidelity sources like Context7 to ensure accuracy in library usage and version-specific features.

## Workflow

### 1. Identify Dependencies and Context
- Scan `requirements.txt`, `package.json`, or relevant source code to determine the exact version of the library in use.
- Identify the specific goal of the research (e.g., "how to use LangChain's EnsembleRetriever").

### 2. High-Fidelity Research (Context7 Priority)
**This is the absolute priority for documentation retrieval.**
1.  **Resolve Library ID:** Call `mcp_context7_resolve-library-id` with the library name (e.g., `langchain`, `django`, `psycopg2`).
2.  **Query Documentation:** Use the resolved ID to call `mcp_context7_query-docs`. Ask specific questions about the feature, usage, and current stable version.
3.  **Cross-Reference Version:** Compare the project's version with the documentation to detect potential deprecations or incompatible features.

### 3. Fallback and Local Research
If Context7 does not yield sufficient information or for niche/private libraries:
- Use `google_web_search` and `web_fetch` to find official documentation and GitHub discussions.
- Search local project files (e.g., `@GEMINI.MD`, `@DOCS/`, or existing `README.md` files) to understand project-specific implementations.

### 4. Synthesis and Reporting
Generate a technical report using the template provided in `references/report_template.md`.

**Deprecation Alert:** Always include a 'Deprecation Alert' section. If the library in the project is significantly behind the latest stable version reported by Context7, provide a clear warning and upgrade path.

## Research Strategy Guide

### Effective Queries
- Instead of "how to use langchain", use "LangChain EnsembleRetriever implementation with ChromaDB and BM25".
- Always include the version number in the query if known: "Django 4.2 QuerySet optimization best practices".

### Troubleshooting with Context7
When encountering errors, use the specific error message as a query parameter in `mcp_context7_query-docs` to find version-specific fixes.

## Resources

### references/
- **[report_template.md](references/report_template.md):** Standardized structure for technical research reports.
