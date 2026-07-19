from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.vectorstore.pinecone_store import vector_store_manager
from app.core.config import settings
import logging
logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        # We initialize the LLM if the API key is present
        self.llm = None
        if settings.GEMINI_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.GEMINI_API_KEY,  # type: ignore
                temperature=0.2
            )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def process_document(self, project_id: str, text: str, source: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Chunks text and adds it to the project's vector store in batches to respect API limits."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        metadatas = [{"source": source} for _ in chunks]
        
        import time
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            chunk_batch = chunks[i:i+batch_size]
            meta_batch = metadatas[i:i+batch_size]
            vector_store_manager.add_texts(project_id, chunk_batch, meta_batch)
            
            if i + batch_size < len(chunks):
                logger.info(f"Rate limit prevention: sleeping for 60 seconds before next batch...")
                time.sleep(60)
                
        return len(chunks)

    async def answer_question(self, project_id: str, question: str, top_k: int = 20) -> dict:
        """Retrieves context and generates an answer."""
        if not self.llm:
            return {"answer": "Error: GEMINI_API_KEY is not set in backend/.env", "sources": []}

        store = vector_store_manager.get_store(project_id)
        if not store:
            return {"answer": "I don't have any documents to read from yet! Please ingest some documents first.", "sources": []}

        import asyncio
        # Retrieve top K most relevant chunks (running in a thread to avoid blocking FastAPI)
        try:
            docs = await asyncio.wait_for(
                asyncio.to_thread(store.similarity_search, question, k=top_k),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.error("Similarity search timed out.")
            return {"answer": "I'm sorry, retrieving context timed out. This may happen if the Gemini API is rate-limited. Please try again in a moment.", "sources": []}

        
        context = "\n\n".join([f"Source: {doc.metadata.get('source', 'Unknown')}\nContent: {doc.page_content}" for doc in docs])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an intelligent technical documentation assistant. You MUST answer the user's question accurately using ONLY the following retrieved context. If you use the context, you must append the source URLs at the very end of your response. If there are multiple sources, you MUST list each one as a separate bullet point. You MUST format EACH source exactly like this:\n\n* <span style='color: gray'>Source:</span> [URL]\n\nIf the answer is NOT contained in the context, you MUST NOT answer the question. Instead, you must say exactly: 'The answer to this question was not found in the ingested documentation.'\n\nContext:\n{context}"),
            ("user", "{question}")
        ])

        chain = prompt | self.llm
        
        try:
            import asyncio
            response = await asyncio.wait_for(
                chain.ainvoke({"context": context, "question": question}),
                timeout=15.0
            )
            
            # Extract unique sources
            sources = list(set([doc.metadata.get('source', 'Unknown') for doc in docs]))
            
            return {
                "answer": response.content,
                "sources": sources
            }
        except asyncio.TimeoutError:
            logger.error("LLM invocation timed out.")
            return {"answer": "I'm sorry, the AI model timed out. This may happen if the Gemini API is rate-limited. Please try again in a moment.", "sources": []}
        except Exception as e:
            logger.error(f"Error during LLM invocation: {e}")
            return {"answer": "An error occurred while communicating with the AI model.", "sources": []}

rag_pipeline = RAGPipeline()
