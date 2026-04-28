# RAG Indexing Logic (ETL)

## Overview
The indexing logic must ensure consistency between semantic and lexical representations for high-precision retrieval.

## 1. Document Chunking Strategy
Use `RecursiveCharacterTextSplitter` with balanced parameters.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=750,  # Balanced for OpenAI context
    chunk_overlap=150, # Sufficient context overlap
    separators=["\n\n", "\n", ".", " ", ""]
)

def create_chunks(documents, customer_id, source):
    # Add metadata for retrieval filtering
    for doc in documents:
        doc.metadata["customer_id"] = customer_id
        doc.metadata["source"] = source
    return text_splitter.split_documents(documents)
```

## 2. ChromaDB (Semantic) Update
Always target the correct collection using the `customer_id`.

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

def update_chroma(chunks, customer_id, persist_dir):
    vectorstore = Chroma(
        persist_directory=persist_dir,
        collection_name=f"cliente_{customer_id}",
        embedding_function=OpenAIEmbeddings()
    )
    # Upsert logic: consider clearing first if it's a full refresh
    vectorstore.add_documents(chunks)
```

## 3. BM25 (Lexical) Index Generation
Save a separate `.pkl` file for each customer.

```python
from langchain_community.retrievers import BM25Retriever
import pickle

def update_bm25(chunks, customer_id, index_dir):
    # BM25 is built from the same chunks used for Chroma
    retriever = BM25Retriever.from_documents(chunks)
    save_path = f"{index_dir}/{customer_id}_index.pkl"
    # Logic to save the index locally
    # (Note: Standard BM25Retriever needs custom logic for pickling)
```

## Maintenance & Consistency
- **Atomicity:** Kestra should only signal "SUCCESS" to the API once both Chroma and BM25 are updated.
- **Versioning:** Consider storing a hash of the source document to avoid redundant indexing.
