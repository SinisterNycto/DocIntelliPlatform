import asyncio
from typing import List
from pydantic import BaseModel, Field
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.vectorstore.pinecone_store import vector_store_manager
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def _citation_label(metadata: dict) -> str:
    source = (metadata or {}).get("source") or "Unknown"
    page = (metadata or {}).get("page")
    if isinstance(page, float) and page.is_integer():
        page = int(page)
    if isinstance(page, int) and page > 0:
        return f"{source} (page {page})"
    return str(source)

class AnswerWithSources(BaseModel):
    answer: str = Field(description="The detailed answer to the user's question, or 'The answer to this question was not found in the ingested documentation.' if the context does not contain the answer.")
    sources: List[str] = Field(description="A list of unique source URLs used to answer the question. If the answer was not found, this should be an empty list.")

class RAGPipeline:
    def __init__(self):
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

    def process_document(self, project_id: str, text: str, source: str, chunk_size: int = 1000, chunk_overlap: int = 200, page: int = None):
        """Chunks text and adds it to the project's vector store in batches to respect API limits."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        meta = {"source": source}
        if page is not None:
            meta["page"] = page
        metadatas = [dict(meta) for _ in chunks]
        
        vector_store_manager.add_texts(project_id, chunks, metadatas)
                
        return len(chunks)

    async def answer_question(self, project_id: str, question: str, chat_history: list = None, top_k: int = 5) -> dict:
        """Retrieves context and generates an answer."""
        if not self.llm:
            return {"answer": "Error: GEMINI_API_KEY is not set in backend/.env", "sources": []}

        store = vector_store_manager.get_store(project_id)
        if not store:
            return {"answer": "I don't have any documents to read from yet! Please ingest some documents first.", "sources": []}

        standalone_question = question
        if chat_history and len(chat_history) > 0:
            try:
                history_text = ""
                for msg in chat_history[-4:]:
                    role = msg.get("role", "").capitalize()
                    history_text += f"{role}: {msg.get('content', '')}\n"
                    
                condense_prompt = ChatPromptTemplate.from_template(
                    "Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question containing all necessary context (entities, subjects) from the conversation. If the question is already standalone, return it as is.\n\nChat History:\n{chat_history}\nFollow Up Input: {question}\nStandalone question:"
                )
                condense_chain = condense_prompt | self.llm
                response = await asyncio.wait_for(
                    condense_chain.ainvoke({"chat_history": history_text, "question": question}),
                    timeout=5.0
                )
                standalone_question = response.content.strip()
                logger.info(f"Rephrased question for semantic search: {standalone_question}")
            except Exception as e:
                logger.error(f"Error reformulating query: {e}")
                standalone_question = question

        try:
            docs = await asyncio.wait_for(
                asyncio.to_thread(store.similarity_search, standalone_question, k=top_k),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.error("Similarity search timed out.")
            return {"answer": "I'm sorry, retrieving context timed out. This may happen if the Gemini API is rate-limited. Please try again in a moment.", "sources": []}

        context = "\n\n".join([f"Source: {doc.metadata.get('source', 'Unknown')}\nContent: {doc.page_content}" for doc in docs])
        
        system_prompt = "You are an intelligent technical documentation assistant. You MUST answer the user's question accurately using ONLY the following retrieved context. If the answer is NOT contained in the context, you MUST NOT answer the question. Instead, you must state that the answer was not found.\n\nContext:\n{context}"
        
        messages = [("system", system_prompt)]
        
        if chat_history:
            for msg in chat_history:
                if msg.get("role") == "user":
                    content = msg.get("content", "").replace("{", "{{").replace("}", "}}")
                    messages.append(("user", content))
                elif msg.get("role") == "assistant":
                    content = msg.get("content", "").replace("{", "{{").replace("}", "}}")
                    messages.append(("assistant", content))
                    
        messages.append(("user", "{question}"))

        prompt = ChatPromptTemplate.from_messages(messages)

        # Use structured output for robust extraction
        structured_llm = self.llm.with_structured_output(AnswerWithSources)
        chain = prompt | structured_llm
        
        try:
            response_obj = await asyncio.wait_for(
                chain.ainvoke({"context": context, "question": question}),
                timeout=30.0
            )
            
            final_answer = response_obj.answer
            used_sources = []
            if "not found" not in final_answer.lower():
                for doc in docs:
                    label = _citation_label(doc.metadata)
                    if label not in used_sources:
                        used_sources.append(label)
            
            # Cite the chunks that were retrieved, not links invented by the model.
            if used_sources:
                final_answer += "\n\n"
                for s in used_sources:
                    if s.startswith("http://") or s.startswith("https://"):
                        final_answer += f"* <span style='color: gray'>Source:</span> [{s}]({s})\n"
                    else:
                        final_answer += f"* <span style='color: gray'>Source:</span> {s}\n"
            
            return {
                "answer": final_answer,
                "sources": used_sources
            }
        except asyncio.TimeoutError:
            logger.error("LLM invocation timed out.")
            return {"answer": "I'm sorry, the AI model timed out. This may happen if the Gemini Generative API is rate-limited or the network is slow. Please try again in a moment.", "sources": []}
        except Exception as e:
            logger.error(f"Error during LLM invocation: {e}")
            return {"answer": "An error occurred while communicating with the AI model.", "sources": []}

rag_pipeline = RAGPipeline()
