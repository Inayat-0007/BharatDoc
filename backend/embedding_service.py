import os
import logging
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

logger = logging.getLogger(__name__)

# BGE-M3 is the constitution-mandated embedding model for BharatDoc.
# It produces 1024-dimensional dense vectors and supports English + Hindi.
# The Vector(1024) dimension in models.py MUST match this output.
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-m3"
DEFAULT_CROSS_ENCODER = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class EmbeddingService:
    def __init__(self):
        # Bi-Encoder for retrieval — BGE-M3 (1024-dim, multilingual)
        self.model_name = os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)

        # Cross-Encoder for re-ranking (High Intelligence)
        self.cross_model_name = os.getenv("CROSS_ENCODER_MODEL", DEFAULT_CROSS_ENCODER)
        logger.info(f"Loading cross-encoder model: {self.cross_model_name}")
        self.cross_model = CrossEncoder(self.cross_model_name)

        logger.info("Intelligence services loaded.")

    def get_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding for a single string.
        Returns a 1024-dim vector for BGE-M3.
        """
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of strings.
        Returns list of 1024-dim vectors for BGE-M3.
        """
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def compute_relevance_scores(self, query: str, texts: list[str]) -> list[float]:
        """
        Compute high-precision relevance scores for a query and a list of texts.
        Uses the Cross-Encoder model.
        """
        if not texts:
            return []

        # CrossEncoder expects pairs of (query, doc)
        pairs = [[query, text] for text in texts]
        scores = self.cross_model.predict(pairs)

        # Scores are typically logits for this model
        # We apply sigmoid to normalize them to 0-1 range for the Confidence Gate
        probabilities = 1 / (1 + np.exp(-scores))
        return probabilities.tolist()


# Singleton instance
embedding_service = EmbeddingService()
