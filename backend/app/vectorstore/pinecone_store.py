import os
import logging
from langchain_core.embeddings import Embeddings
from langchain_pinecone import PineconeVectorStore
from app.core.config import settings

logger = logging.getLogger(__name__)

# bge-small is 384-d, same width as the previous MiniLM index, so the Pinecone
# index does not need to be recreated. Existing vectors still have to be rebuilt.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class LocalEmbeddings(Embeddings):
    """Sentence-transformer embeddings. Query text gets the bge query prefix; documents do not."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        logger.info(
            "Loading embedding model %s. Re-ingest documents after changing embedding models.",
            model_name,
        )
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(list(texts), normalize_embeddings=True)
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        prompts = getattr(self.model, "prompts", None) or {}
        if "query" in prompts:
            vector = self.model.encode([text], prompt_name="query", normalize_embeddings=True)
        else:
            vector = self.model.encode([BGE_QUERY_PREFIX + text], normalize_embeddings=True)
        return vector[0].tolist()


class VectorStoreManager:
    def __init__(self):
        self._embeddings = None
        self._stores = {}
        self.index_name = settings.PINECONE_INDEX_NAME
        if settings.PINECONE_API_KEY:
            os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = LocalEmbeddings(settings.EMBEDDING_MODEL)
        return self._embeddings

    def get_store(self, project_id: str) -> PineconeVectorStore:
        if not settings.PINECONE_API_KEY:
            logger.error("PINECONE_API_KEY is not set.")
            return None

        store = self._stores.get(project_id)
        if store is None:
            store = PineconeVectorStore(
                index_name=self.index_name,
                embedding=self.embeddings,
                namespace=project_id,
            )
            self._stores[project_id] = store
        return store

    def add_texts(self, project_id: str, texts: list[str], metadatas: list[dict] = None):
        store = self.get_store(project_id)
        if store and texts:
            store.add_texts(texts, metadatas=metadatas)
        elif not store:
            logger.error("Failed to add texts: Pinecone store could not be initialized.")

    def _index(self):
        from pinecone import Pinecone

        return Pinecone(api_key=settings.PINECONE_API_KEY).Index(self.index_name)

    def delete_namespace(self, project_id: str):
        store = self.get_store(project_id)
        if store:
            try:
                store.delete(delete_all=True, namespace=project_id)
                logger.info("Deleted Pinecone namespace: %s", project_id)
            except Exception as e:
                logger.error("Error deleting namespace %s: %s", project_id, e)
        else:
            logger.error("Failed to delete namespace: Pinecone store could not be initialized.")

    def delete_document(self, project_id: str, document_id: str, source: str):
        """Remove chunks for this document. Source filter covers vectors ingested before document_id existed."""
        if not settings.PINECONE_API_KEY:
            logger.error("PINECONE_API_KEY is not set.")
            return

        index = self._index()
        filters = []
        if document_id:
            filters.append({"document_id": {"$eq": str(document_id)}})
        if source:
            filters.append({"source": {"$eq": source}})
        for metadata_filter in filters:
            try:
                index.delete(filter=metadata_filter, namespace=project_id)
            except Exception as e:
                logger.error("Error deleting vectors %s in %s: %s", metadata_filter, project_id, e)


vector_store_manager = VectorStoreManager()
