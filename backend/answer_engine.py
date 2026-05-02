"""
Phase 11: Answer Engine
Extractive answering with optional Ollama LLM synthesis.

Architecture:
1. EXTRACTIVE MODE (default, always available):
   - Selects the most relevant span from top-k chunks
   - Returns direct text extraction — zero hallucination risk
   
2. SYNTHESIS MODE (optional, requires Ollama):
   - Feeds top-k chunks + query to a local LLM via Ollama
   - Strict system prompt: answer from context ONLY
   - Falls back to extractive if Ollama is unavailable

The answer engine is called ONLY if the confidence gate passes.
"""

import os
import re
import logging
import httpx
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))
USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"

# The strict system prompt — never change the intent
SYSTEM_PROMPT = """You are a document question-answering assistant. You MUST follow these rules EXACTLY:

1. Answer ONLY using the provided context passages. Never use external knowledge.
2. If the context does not contain enough information to answer the question, respond EXACTLY with: "This information is not present in the uploaded document."
3. Never invent, assume, or hallucinate information not explicitly stated in the context.
4. Never invent citations or page numbers. Only reference what is given.
5. Keep answers concise and directly relevant to the question.
6. If the context partially answers the question, answer only the part that is supported and clearly state what is not covered.

CONTEXT PASSAGES:
{context}

QUESTION: {question}

ANSWER:"""


@dataclass
class AnswerResult:
    """Result from the answer engine."""
    answer: str
    mode: str  # "extractive" or "synthesis"
    source_chunks: list[dict] = field(default_factory=list)


class AnswerEngine:
    """
    Document Q&A answer engine.
    
    Supports two modes:
    - Extractive: returns the most relevant chunk text directly
    - Synthesis: uses a local Ollama LLM to synthesize an answer from chunks
    """
    
    def __init__(self):
        self.use_llm = USE_LLM
        self.ollama_url = OLLAMA_BASE_URL
        self.ollama_model = OLLAMA_MODEL
        self.ollama_timeout = OLLAMA_TIMEOUT
        
        if self.use_llm:
            logger.info(f"AnswerEngine: LLM mode enabled (model={self.ollama_model}, url={self.ollama_url})")
        else:
            logger.info("AnswerEngine: Extractive-only mode (USE_LLM=false)")
    
    def generate_answer(
        self,
        query: str,
        chunks: list[dict],
        confidence_score: float
    ) -> AnswerResult:
        """
        Generate an answer from retrieved chunks.
        
        Args:
            query: The user's question
            chunks: List of dicts with 'text', 'page_number', 'chunk_index', 'similarity'
            confidence_score: From the confidence gate (0-1)
        
        Returns:
            AnswerResult with the answer and metadata
        """
        if not chunks:
            return AnswerResult(
                answer="This information is not present in the uploaded document.",
                mode="extractive",
                source_chunks=[]
            )
        
        # Try LLM synthesis if enabled
        if self.use_llm:
            try:
                return self._synthesize_answer(query, chunks)
            except Exception as e:
                logger.warning(f"LLM synthesis failed, falling back to extractive: {e}")
        
        # Default: extractive answer
        return self._extractive_answer(query, chunks)
    
    def _extractive_answer(self, query: str, chunks: list[dict]) -> AnswerResult:
        """
        Extractive answering: find the best matching span in the top chunks.
        
        Strategy:
        1. Use top-3 chunks (already sorted by similarity)
        2. For each chunk, find sentences containing query terms
        3. Return the most relevant sentences as the answer
        """
        query_terms = set(self._tokenize(query))
        
        best_sentences = []
        
        for chunk_data in chunks[:3]:
            text = chunk_data["text"]
            sentences = self._split_sentences(text)
            
            for sentence in sentences:
                sentence_terms = set(self._tokenize(sentence))
                overlap = len(query_terms & sentence_terms)
                if overlap > 0:
                    best_sentences.append((overlap, sentence, chunk_data))
        
        # Sort by overlap count (descending)
        best_sentences.sort(key=lambda x: x[0], reverse=True)
        
        if best_sentences:
            # Take top 3-5 most relevant sentences
            selected = best_sentences[:5]
            answer_parts = []
            seen = set()
            for _, sentence, _ in selected:
                normalized = sentence.strip()
                if normalized not in seen:
                    answer_parts.append(normalized)
                    seen.add(normalized)
            
            answer = " ".join(answer_parts)
        else:
            # No sentence-level match, return the top chunk directly
            answer = chunks[0]["text"]
        
        return AnswerResult(
            answer=answer,
            mode="extractive",
            source_chunks=[
                {
                    "page_number": c["page_number"],
                    "chunk_index": c["chunk_index"],
                    "similarity": c["similarity"]
                }
                for c in chunks[:5]
            ]
        )
    
    def _synthesize_answer(self, query: str, chunks: list[dict]) -> AnswerResult:
        """
        LLM synthesis via Ollama.
        
        Sends the top chunks + query to a local LLM with a strict system prompt.
        """
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks[:5]):
            context_parts.append(
                f"[Passage {i+1}, Page {chunk['page_number']}]\n{chunk['text']}"
            )
        context = "\n\n".join(context_parts)
        
        # Build the prompt
        prompt = SYSTEM_PROMPT.format(context=context, question=query)
        
        # Call Ollama API
        try:
            with httpx.Client(timeout=self.ollama_timeout) as client:
                response = client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Low temperature for factual answers
                            "top_p": 0.9,
                            "num_predict": 512,  # Max output tokens
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                answer = result.get("response", "").strip()
                
                if not answer:
                    raise ValueError("Empty response from Ollama")
                
                logger.info(f"LLM synthesis succeeded ({len(answer)} chars)")
                
                return AnswerResult(
                    answer=answer,
                    mode="synthesis",
                    source_chunks=[
                        {
                            "page_number": c["page_number"],
                            "chunk_index": c["chunk_index"],
                            "similarity": c["similarity"]
                        }
                        for c in chunks[:5]
                    ]
                )
                
        except httpx.ConnectError:
            logger.warning("Ollama not reachable — falling back to extractive")
            raise
        except httpx.HTTPStatusError as e:
            logger.warning(f"Ollama HTTP error {e.response.status_code} — falling back")
            raise
        except Exception as e:
            logger.warning(f"Ollama error: {e} — falling back to extractive")
            raise
    
    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences using basic punctuation rules."""
        # Split on sentence-ending punctuation followed by space or newline
        sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization for overlap matching."""
        stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "can", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "and", "but",
            "or", "not", "so", "yet", "both", "each", "all", "any",
            "than", "too", "very", "just", "about", "up", "down", "out",
            "off", "over", "under", "again", "then", "once", "here",
            "there", "when", "where", "why", "how", "what", "which",
            "who", "whom", "this", "that", "these", "those", "it", "its",
            "i", "me", "my", "we", "our", "you", "your", "he", "him",
            "his", "she", "her", "they", "them", "their"
        }
        tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())
        return [t for t in tokens if len(t) > 2 and t not in stopwords]
    
    def check_ollama_available(self) -> bool:
        """Check if Ollama is reachable and has the configured model."""
        if not self.use_llm:
            return False
        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{self.ollama_url}/api/tags")
                if resp.status_code == 200:
                    models = [m["name"] for m in resp.json().get("models", [])]
                    available = self.ollama_model in models
                    logger.info(f"Ollama available={available}, models={models}")
                    return available
            return False
        except Exception:
            return False


# Singleton
answer_engine = AnswerEngine()
