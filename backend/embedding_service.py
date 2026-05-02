import os
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        # We use a lightweight model for MVP/local deployment
        self.model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        logger.info("Embedding model loaded.")
        
    def get_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding for a single string.
        """
        # encode returns a numpy array, convert to list for pgvector
        embedding = self.model.encode(text)
        return embedding.tolist()
        
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of strings.
        """
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

# Singleton instance to be used across the app
embedding_service = EmbeddingService()
