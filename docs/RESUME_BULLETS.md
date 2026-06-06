# SourceLens resume bullets

Use only the bullets that match the resume space available and the role you are targeting.

## Six possible bullets

- Built **SourceLens**, a Streamlit application for conversational search across multiple PDFs using Python, `pypdf`, OpenAI embeddings, and a local NumPy vector index.
- Implemented a retrieval-augmented generation pipeline that chunks PDF text, embeds document passages, ranks top-k matches with cosine similarity, and sends retrieved context to the OpenAI Responses API.
- Preserved filename and page-level metadata throughout PDF extraction and retrieval, allowing users to inspect referenced passages beneath each generated answer.
- Added session controls for rebuilding a PDF collection, starting a new conversation without discarding the index, and removing indexed documents from memory.
- Handled missing API keys, empty questions, corrupted PDFs, encrypted files, blank pages, and image-only scans with clear user-facing validation messages.
- Wrote automated tests with `pytest` for configuration parsing, text chunking, PDF metadata retention, vector ranking, embedding batching, and response-generation wiring.

## Strongest three bullets

- Built **SourceLens**, a Streamlit application for conversational search across multiple PDFs using Python, `pypdf`, OpenAI embeddings, and a local NumPy vector index.
- Implemented a retrieval-augmented generation pipeline that chunks PDF text, ranks top-k passages with cosine similarity, and generates grounded answers through the OpenAI Responses API.
- Preserved document names and page references throughout retrieval and added `pytest` coverage for preprocessing, ranking, validation, and OpenAI-service integration behavior.

## Recommended final project entry

**SourceLens** | Python, Streamlit, OpenAI API, NumPy, pypdf, pytest  
- Built a Streamlit application for conversational search across multiple PDFs using OpenAI embeddings and a local NumPy vector index.  
- Implemented a retrieval-augmented generation pipeline that chunks PDF text, ranks top-k passages with cosine similarity, and generates grounded answers through the OpenAI Responses API.  
- Preserved document names and page references throughout retrieval and added `pytest` coverage for preprocessing, ranking, validation, and OpenAI-service integration behavior.

## AI / data research resume version

**SourceLens** | Python, OpenAI API, NumPy, pypdf, Streamlit  
- Implemented a retrieval-augmented PDF question-answering workflow using OpenAI embeddings, overlapping text chunks, and cosine-similarity ranking in NumPy.  
- Preserved page-level provenance for retrieved passages and exposed ranked source excerpts alongside generated answers for easier inspection.  
- Tested preprocessing, embedding batching, ranking behavior, and edge-case validation with `pytest` and mocked API clients.

## Interdisciplinary computational-research resume version

**SourceLens** | Python, Streamlit, OpenAI API, NumPy, pypdf  
- Developed a PDF exploration tool that supports natural-language questions across multi-document collections and surfaces the supporting document pages for each response.  
- Designed a transparent text-processing pipeline that extracts readable pages, creates overlapping passages, generates embeddings, and retrieves relevant evidence with cosine similarity.  
- Added validation for unreadable documents, blank pages, encrypted files, and unsupported scanned PDFs to make document processing behavior easier to interpret.

## Software engineering / information systems / HCI resume version

**SourceLens** | Python, Streamlit, OpenAI API, NumPy, pypdf, pytest  
- Built a Streamlit multi-PDF search interface with collection status, document metrics, conversational history, source expanders, and session reset controls.  
- Refactored PDF processing, local retrieval, API integration, configuration, and UI helpers into focused Python modules with environment-based settings.  
- Added automated tests and user-facing error handling for common setup, document-processing, and input-validation failures.
