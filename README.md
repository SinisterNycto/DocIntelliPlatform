### DocIntelliPlatform
> An autonomous RAG (Retrieval-Augmented Generation) platform designed to process, vectorize, and query technical documentation using local Hugging Face embeddings, Pinecone, and Gemini 3.8 Flash. When a document is ingested, the engine chunks, embeds, and indexes the content locally, providing a highly technical chat interface for instant semantic retrieval with exact source citations.

## 1. Features
* **Isolated, multi-tenant workspaces:** Complete namespace separation ensuring data privacy across multiple user accounts via Clerk JWT authentication.
* **Conversational Memory:** AI RAG pipeline automatically retrieves historical chat context for seamless follow-up questions.
* **Rich Markdown UI:** Custom frontend rendering for GitHub Flavored Markdown, properly displaying bash commands, code blocks, and structured tables.
* Complete workspace deletion with cascading cleanup across MongoDB and Pinecone vector stores.
* Dynamic data ingestion pipelines supporting complex Single Page Applications (SPAs) via Jina Reader API and raw PDF uploads.
* Fully automated, asynchronous vectorization pipeline using Celery workers that chunks large documents and pushes embeddings directly to Pinecone.
* Intelligent RAG querying with strict, unique source citations to prevent LLM hallucination.
* Real-time UI dashboard tracking the status of ingestion pipelines and semantic search context.

## 2. Architecture
The application follows a robust decoupled architecture. A FastAPI backend orchestrates the complex RAG pipelines using LangChain, relying on MongoDB for metadata tracking and Pinecone as a highly scalable semantic vector index. 

Instead of relying on cloud providers for embeddings, the backend runs a local Hugging Face model (`BAAI/bge-small-en-v1.5`) via `sentence-transformers` within the Docker container for unlimited, rate-limit-free vectorization, then reranks the top matches before answering. It communicates with the Google Gemini API (`gemini-3.8-flash`) exclusively for the final generative text capabilities. Finally, a React+Vite frontend visualizes these isolated workspaces and provides a terminal-inspired, data-dense query interface.

## 3. Tech Stack

| Layer | Technology |
| --- | --- |
| **Frontend** | React, Vite, TypeScript, Tailwind CSS, React Query, Clerk Auth |
| **Backend** | Python, FastAPI, Uvicorn, Celery |
| **AI (Embeddings)** | Hugging Face (`BAAI/bge-small-en-v1.5`), `BAAI/bge-reranker-base`, `sentence-transformers` |
| **AI (Generative)** | Google Gemini API (`gemini-3.8-flash`), LangChain |
| **Database** | MongoDB, Redis (Celery Broker) |
| **Vector Store** | Pinecone |
| **Authentication** | Clerk (JWT parsing in FastAPI) |
| **Deployment** | Docker, Docker Compose |

## 4. Setup & Running locally

### Prerequisites
* Docker and Docker Compose
* A Pinecone account and API Key
* A Google Cloud / Gemini account and API Key

### Steps
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd <repo-dir>
   ```

2. Set up environment variables:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and fill in your Gemini API Key, Pinecone API Key, and Index Name
   ```

3. Run the application:

**Using Docker (Recommended)**
   ```bash
   docker-compose up --build
   ```

4. The backend API will be available at `http://localhost:8000` (Swagger docs at `/docs`) and the frontend dashboard at `http://localhost:5173`

## 5. How it works
1. **Namespace initialized:** A developer creates a new workspace on the dashboard. The backend provisions an isolated namespace in MongoDB.
2. **Data ingested:** The user submits a URL or PDF. A background Celery worker scrapes the text (using Jina Reader for complex websites) or extracts PDF text, running it through a `RecursiveCharacterTextSplitter`.
3. **Automated Local Vectorization:** LangChain sends the document chunks through the local Hugging Face pipeline, maps the 384-dimensional semantic vectors, and upserts them directly to the designated Pinecone namespace.
4. **Context-aware Querying:** When a user asks a question, the backend embeds the query locally, executes a similarity search against Pinecone, reranks the candidates, and sends only those chunks to Gemini. Citations are taken from the retrieved chunk metadata. Previous conversational history is used to rewrite follow-up questions before search.

Changing `EMBEDDING_MODEL` does not resize the Pinecone index (`bge-small-en-v1.5` is 384-dimensional, same as the previous MiniLM model), but old vectors are not compatible with the new model. Create a new project, or delete and re-upload documents, before judging answer quality on this branch.

## 6. Known Limitations

**1. Third-Party AI Data Privacy**
For this portfolio project, the backend is integrated with the public Google Gemini API for final text generation. In a true enterprise environment, sending proprietary corporate data to a public consumer LLM is a strict security violation. 
* *Enterprise Fix:* To deploy this for an enterprise, the public Gemini API endpoint would be swapped for an on-premise open-source model (like Llama 3) to guarantee strict SOC2 and data privacy compliance.

**2. Managed Vector Database Costs**
The platform currently relies on Pinecone's managed Serverless infrastructure for vector storage, which can become prohibitively expensive at massive enterprise scale.
* *Enterprise Fix:* In a production environment with millions of vectors, the architecture would be adapted to use a self-hosted vector solution like PostgreSQL with the `pgvector` extension or an open-source Milvus cluster deployed securely within the enterprise's private VPC.
