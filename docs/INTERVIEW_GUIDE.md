# SourceLens interview guide

## 45-second explanation

SourceLens is a Streamlit application that lets a user ask questions across multiple PDF documents. When the user builds an index, the app extracts readable text page by page, splits it into overlapping chunks, generates OpenAI embeddings, and stores the normalized vectors in a local in-memory NumPy index. For each question, it embeds the query, retrieves the most relevant chunks with cosine similarity, sends those passages to an OpenAI chat model through the Responses API, and displays both the answer and the supporting document names and page numbers.

## 90-second explanation

SourceLens is a revised version of a multi-PDF question-answering project. The goal was to keep the retrieval-augmented generation workflow understandable instead of hiding it behind a large abstraction. A user uploads one or more PDFs through Streamlit and selects **Build Document Index**. The preprocessing layer reads each PDF with `pypdf`, extracts text page by page, cleans spacing noise, and creates overlapping chunks while retaining the source filename and page number. The OpenAI embeddings API converts those chunks into vectors. SourceLens normalizes the vectors and stores them in a lightweight in-memory NumPy index. When a user asks a question, the app embeds that question, calculates cosine-similarity scores, retrieves the top-ranked passages, and sends only those passages, the current question, and a small amount of recent chat history to the OpenAI Responses API. The UI then displays the generated answer and an expandable list of referenced passages. I also added validation for empty questions, missing API keys, corrupted PDFs, encrypted files, image-only scans, and reset actions for the chat or the entire collection.

## Data flow

```text
Uploaded PDFs
    ↓
pypdf page-by-page text extraction
    ↓
Cleaned page text with filename and page metadata
    ↓
Overlapping text chunks
    ↓
OpenAI text embeddings
    ↓
Normalized vectors stored in an in-memory NumPy index
    ↓
User question → question embedding
    ↓
Cosine-similarity search → top-k passages
    ↓
Retrieved passages + recent chat history + question
    ↓
OpenAI Responses API
    ↓
Answer + expandable source passages
```

## Major libraries and why they were used

| Library | Purpose |
|---|---|
| `streamlit` | Provides the upload controls, sidebar collection state, chat interface, and expandable source display. |
| `pypdf` | Extracts text from readable PDF pages. |
| `openai` | Calls the embeddings endpoint and the Responses API. |
| `numpy` | Stores normalized embeddings and performs cosine-similarity ranking locally. |
| `python-dotenv` | Loads the API key and configuration values from a local `.env` file. |
| `pytest` | Runs focused tests for configuration, PDF preprocessing, retrieval, and the OpenAI wrapper with fake clients. |

## Most important files

| File | Why it matters |
|---|---|
| `app.py` | Coordinates Streamlit state, indexing, chat interactions, and reset actions. |
| `src/pdf_processing.py` | Extracts page text and creates overlapping chunks with metadata. |
| `src/retrieval.py` | Implements the in-memory cosine-similarity vector index. |
| `src/openai_service.py` | Wraps embeddings and answer generation and constructs grounded prompts. |
| `src/models.py` | Defines the data structures passed between layers. |
| `tests/` | Shows which behaviors are verified without making live API calls. |

## Ten likely technical questions and honest answers

### 1. Why split PDF text into chunks?
A full PDF can be too large and too unfocused to pass into a model for every question. Chunking creates smaller searchable units so the app can retrieve only the passages most relevant to the current question.

### 2. Why use overlapping chunks?
A sentence or idea may fall near the boundary between two chunks. A modest overlap reduces the chance that important context is split apart and lost during retrieval.

### 3. How do you preserve source information?
Text is extracted page by page. Every chunk stores its source filename and page number. When a chunk is retrieved, those metadata fields are displayed with the referenced passage.

### 4. How does semantic retrieval work?
The app embeds each document chunk and the user question into vectors. It normalizes those vectors and calculates cosine similarity with a matrix multiplication. The highest-scoring chunks are used as context for answer generation.

### 5. Why use a NumPy index instead of a database?
The project is intentionally local and session-based. A NumPy matrix keeps the retrieval logic visible and avoids adding a database for a moderate document collection. For larger collections or persistence, a dedicated vector database would be a reasonable next step.

### 6. Does the model see every uploaded PDF on every question?
No. During indexing, chunk text is sent to the embeddings API. During question answering, the app sends the current question, a small amount of recent chat history, and the top retrieved passages to the response model.

### 7. How do you prevent unsupported answers?
The system instruction tells the model to answer only from the retrieved PDF passages and to state when the passages are insufficient. The UI also shows the retrieved passages so the user can inspect the support directly. This reduces unsupported answers but does not guarantee perfect factual accuracy.

### 8. How do follow-up questions work?
The app includes a configurable number of recent user and assistant messages in the answer-generation prompt. Retrieval is still performed for each new question, so the generated answer remains connected to PDF passages.

### 9. What PDFs are not supported well?
Image-only scans are the main limitation because ordinary PDF text extraction cannot read text that exists only as pixels. Password-protected PDFs are also skipped. OCR could be added later for scanned documents.

### 10. What did you test?
The automated tests cover environment validation, metadata retention during extraction, blank and corrupted PDF handling, chunking, retrieval ranking, dimension validation, embedding batching, prompt construction, Responses API wiring with a fake client, and empty-question validation. Live OpenAI calls are intentionally left for manual testing so the test suite does not consume API credits.

## Realistic technical challenge

The original version combined all extracted text into one string before chunking. That made it difficult to show reliable source references. The revised version extracts text page by page and carries filename and page metadata through chunking, retrieval, and rendering. That required treating document chunks as structured records instead of plain strings.

## Limitation

The vector index exists only in memory for the active Streamlit session. Closing the app or removing the collection discards the index, so the PDFs need to be processed again later.

## Two reasonable future improvements

1. Add OCR as an optional preprocessing path for scanned image-only PDFs.
2. Add local persistence so a user can save and reopen a processed document collection without regenerating embeddings.

## How this differs from the original version

The revised version has a new product identity and a different interface structure. It replaces custom avatar HTML with native Streamlit chat components, preserves filename and page metadata, exposes referenced passages, adds collection metrics and reset controls, handles common errors, uses environment configuration, includes tests, and makes the retrieval pipeline explicit with a small local NumPy vector index rather than relying on a high-level conversational chain.
