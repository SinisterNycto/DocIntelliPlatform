import asyncio
from typing import List
from pydantic import BaseModel, Field
from langchain_text_splitters import MarkdownTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.vectorstore.pinecone_store import vector_store_manager
from app.core.config import settings
from app.rag.citations import (
    answer_was_not_found,
    append_sources,
    citation_labels,
    history_without_current_question,
    message_text,
)
import logging

logger = logging.getLogger(__name__)


class AnswerWithSources(BaseModel):
    answer: str = Field(
        description="The detailed answer to the user's question, or 'The answer to this question was not found in the ingested documentation.' if the context does not contain the answer."
    )


class RAGPipeline:
    def __init__(self):
        self.llm = None
        self._reranker = None
        if settings.GEMINI_API_KEY:
            # Gemini 3 uses thinking_level. Keep temperature low so answers stay tied to the docs.
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                api_key=settings.GEMINI_API_KEY,
                temperature=0.2,
                thinking_level="low",
            )
            logger.info("Generative model: %s", settings.GEMINI_MODEL)

    def _splitter(self, chunk_size: int, chunk_overlap: int) -> MarkdownTextSplitter:
        return MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def build_chunks(self, parts: list, chunk_size: int = 1000, chunk_overlap: int = 200):
        splitter = self._splitter(chunk_size, chunk_overlap)
        texts = []
        metadatas = []
        for text, meta in parts:
            for chunk in splitter.split_text(text or ""):
                if not chunk.strip():
                    continue
                texts.append(chunk)
                metadatas.append(dict(meta))
        return texts, metadatas

    def process_parts(self, project_id: str, parts: list, chunk_size: int = 1000, chunk_overlap: int = 200):
        texts, metadatas = self.build_chunks(parts, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        vector_store_manager.add_texts(project_id, texts, metadatas)
        return len(texts)

    def process_document(self, project_id: str, text: str, source: str, chunk_size: int = 1000, chunk_overlap: int = 200, document_id: str = None, page: int = None):
        """Chunks text and adds it to the project's vector store."""
        meta = {"source": source}
        if document_id:
            meta["document_id"] = str(document_id)
        if page is not None:
            meta["page"] = page
        return self.process_parts(project_id, [(text, meta)], chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def _rerank(self, question: str, docs: list, top_k: int) -> list:
        if not docs:
            return []
        if not settings.RERANK_ENABLED or len(docs) == 1:
            return docs[:top_k]
        try:
            if self._reranker is None:
                from sentence_transformers import CrossEncoder

                logger.info("Loading reranker %s", settings.RERANK_MODEL)
                self._reranker = CrossEncoder(settings.RERANK_MODEL)
            pairs = [(question, doc.page_content) for doc in docs]
            scores = self._reranker.predict(pairs)
            ranked = [doc for _, doc in sorted(zip(scores, docs), key=lambda item: float(item[0]), reverse=True)]
            return ranked[:top_k]
        except Exception as e:
            logger.error("Reranking failed, using vector order: %s", e)
            return docs[:top_k]

    async def answer_question(self, project_id: str, question: str, chat_history: list = None, top_k: int = 5) -> dict:
        """Retrieves context and generates an answer. Citations come from retrieved chunks, not the model."""
        if not self.llm:
            return {"answer": "Error: GEMINI_API_KEY is not set in backend/.env", "sources": []}

        store = vector_store_manager.get_store(project_id)
        if not store:
            return {"answer": "I don't have any documents to read from yet! Please ingest some documents first.", "sources": []}

        prior_history = history_without_current_question(chat_history or [], question)
        standalone_question = question
        if prior_history:
            try:
                history_text = ""
                for msg in prior_history[-4:]:
                    role = msg.get("role", "").capitalize()
                    history_text += f"{role}: {msg.get('content', '')}\n"

                condense_prompt = ChatPromptTemplate.from_template(
                    "Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question containing all necessary context (entities, subjects) from the conversation. If the question is already standalone, return it as is.\n\nChat History:\n{chat_history}\nFollow Up Input: {question}\nStandalone question:"
                )
                condense_chain = condense_prompt | self.llm
                response = await asyncio.wait_for(
                    condense_chain.ainvoke({"chat_history": history_text, "question": question}),
                    timeout=20.0,
                )
                standalone_question = message_text(response) or question
                logger.info("Rephrased question for semantic search: %s", standalone_question)
            except Exception as e:
                logger.error("Error reformulating query: %s", e)
                standalone_question = question

        candidate_k = max(top_k, settings.RETRIEVAL_CANDIDATES)
        try:
            docs = await asyncio.wait_for(
                asyncio.to_thread(store.similarity_search, standalone_question, k=candidate_k),
                timeout=20.0,
            )
        except asyncio.TimeoutError:
            logger.error("Similarity search timed out.")
            return {"answer": "I'm sorry, searching the document index timed out. Please try again in a moment.", "sources": []}

        docs = await asyncio.to_thread(self._rerank, standalone_question, docs, top_k)
        if not docs:
            return {
                "answer": "I don't have any matching documentation for that question. Please ingest a document and try again.",
                "sources": [],
            }

        context = "\n\n".join(
            [f"Source: {citation_labels([doc])[0]}\nContent: {doc.page_content}" for doc in docs]
        )

        system_prompt = "You are an intelligent technical documentation assistant. You MUST answer the user's question accurately using ONLY the following retrieved context. If the answer is NOT contained in the context, you MUST NOT answer the question. Instead, you must state that the answer was not found.\n\nContext:\n{context}"

        messages = [("system", system_prompt)]
        for msg in prior_history[-6:]:
            role = msg.get("role")
            if role not in {"user", "assistant"}:
                continue
            content = msg.get("content", "").replace("{", "{{").replace("}", "}}")
            messages.append((role, content))
        messages.append(("user", "{question}"))

        prompt = ChatPromptTemplate.from_messages(messages)
        structured_llm = self.llm.with_structured_output(AnswerWithSources)
        chain = prompt | structured_llm

        try:
            response_obj = await asyncio.wait_for(
                chain.ainvoke({"context": context, "question": question}),
                timeout=45.0,
            )
            if isinstance(response_obj, dict):
                final_answer = response_obj.get("answer") or ""
            else:
                final_answer = response_obj.answer

            labels: List[str] = [] if answer_was_not_found(final_answer) else citation_labels(docs)
            if labels:
                final_answer = append_sources(final_answer, labels)

            return {"answer": final_answer, "sources": labels}
        except asyncio.TimeoutError:
            logger.error("LLM invocation timed out.")
            return {"answer": "I'm sorry, the AI model timed out before it could answer. Please try again in a moment.", "sources": []}
        except Exception as e:
            logger.error("Error during LLM invocation: %s", e)
            return {"answer": "An error occurred while communicating with the AI model.", "sources": []}


rag_pipeline = RAGPipeline()
