# RAG Precision & Quality Review

## 1. Retrieval Strategy (Hybrid)
- [ ] Both `Chroma` (semantic) and `BM25` (lexical) retrievers are combined via `EnsembleRetriever`.
- [ ] Weights are balanced: `[0.6, 0.4]` for conversational context, `[0.5, 0.5]` for technical/medical term extraction.
- [ ] Results are re-ranked (optional but recommended for precision).

## 2. Chunking Logic (Kestra / ETL)
- [ ] Chunk size is appropriate for the LLM context window (e.g., 500-1000 tokens).
- [ ] Chunk overlap (e.g., 10-15%) is used to maintain context continuity.
- [ ] Metadata (e.g., source file, section title, page number) is preserved in chunks.

## 3. Query Processing
- [ ] Queries are cleaned (removal of emojis, "good morning" fluff) before being sent to the retriever.
- [ ] Multi-query retrieval (optional) is implemented to expand the search scope for vague user messages.

## 4. Synthesis & Response
- [ ] Source attribution: The LLM is instructed to cite sources (e.g., "According to the clinic's policy...").
- [ ] Confidence check: The LLM responds with "I don't have this information" if retrieval score is below a defined threshold.
