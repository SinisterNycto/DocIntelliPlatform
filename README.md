### DocIntelliPlatform
> An autonomous RAG (Retrieval-Augmented Generation) platform designed to process, vectorize, and query technical documentation using Gemini and Pinecone. When a document is ingested, the engine chunks, embeds, and indexes the content, providing a highly technical chat interface for instant semantic retrieval with exact source citations.

## 1. Features
* Isolated, multi-project workspaces (namespaces) for managing independent knowledge bases.
* Dynamic data ingestion pipelines supporting both direct web scraping (HTTPS endpoints) and raw PDF uploads.
* Fully automated vectorization pipeline that chunks large documents and pushes embeddings directly to Pinecone.
* Intelligent RAG querying with strict, line-by-line source citations to prevent LLM hallucination.
* Real-time UI dashboard tracking the status of ingestion pipelines and semantic search context.

## 2. Architecture
The application follows a robust decoupled architecture. A FastAPI backend orchestrates the complex RAG pipelines using LangChain, relying on MongoDB for metadata tracking and Pinecone as a highly scalable semantic vector index. It communicates with the Google Gemini API for state-of-the-art embeddings and generative capabilities. Finally, a React+Vite frontend visualizes these isolated workspaces and provides a terminal-inspired, data-dense query interface.

## 3. Tech Stack

| Layer | Technology |
| --- | --- |
| **Frontend** | React, Vite, TypeScript, Tailwind CSS, React Query |
| **Backend** | Python, FastAPI, Uvicorn, Motor (Async) |
| **AI** | Google Gemini API (`gemini-embedding-2`, `gemini-2.5-flash`), LangChain |
| **Database** | MongoDB |
| **Vector Store** | Pinecone |
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

4. The backend API will be available at `http://localhost:8000` (Swagger docs at `/docs`) and the frontend dashboard at `http://localhost:5173`. 

## 5. How it works
1. **Namespace initialized:** A developer creates a new workspace on the dashboard. The backend provisions an isolated namespace in MongoDB.
2. **Data ingested:** The user submits a URL or PDF. The FastAPI backend scrapes or extracts the text, running it through a `RecursiveCharacterTextSplitter`.
3. **Automated Vectorization:** LangChain sends the document chunks to the Gemini Embeddings API, maps the semantic vectors, and upserts them directly to the designated Pinecone namespace.
4. **Context-aware Querying:** When a user asks a question, the backend embeds the query, executes a similarity search against Pinecone, and injects the top-K semantic matches directly into the Gemini LLM prompt to synthesize a highly accurate answer.

## 6. Future Improvements
* Replace managed Google Embeddings with local Hugging Face embedding models to eliminate rate-limit bottlenecks.
* Implement user authentication and RBAC (Role-Based Access Control) for secure team collaboration.
* Add direct GitHub repository ingestion to automatically index and chat with entire codebases.
* Deploy self-hosted `pgvector` or Milvus to replace managed Pinecone instances.

## 7. Known Limitations

**1. Third-Party AI Data Privacy**
For this portfolio project, the backend is integrated with the public Google Gemini API. In a true enterprise environment, sending proprietary corporate data to a public consumer LLM is a strict security violation. 
* *Enterprise Fix:* To deploy this for an enterprise, the public Gemini API endpoint would be swapped for a Zero-Retention Enterprise API (like Azure OpenAI or Google Cloud Vertex AI) or an on-premise open-source model (like Llama 3) to guarantee strict SOC2 and data privacy compliance.

**2. Managed Vector Database Costs**
The platform currently relies on Pinecone's managed Serverless infrastructure for vector storage, which can become prohibitively expensive at massive enterprise scale.
* *Enterprise Fix:* In a production environment with millions of vectors, the architecture would be adapted to use a self-hosted vector solution like PostgreSQL with the `pgvector` extension or an open-source Milvus cluster deployed securely within the enterprise's private VPC.
