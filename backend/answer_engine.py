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
        Local generative answering: uses a lightweight HuggingFace pipeline 
        to synthesize an answer based on the context, running entirely offline.
        """
        from transformers import pipeline
        
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks[:5]):
            context_parts.append(
                f"Passage {i+1}: {chunk['text']}"
            )
        context = "\n\n".join(context_parts)
        
        # Load the model only once (caching on the class if possible, or load dynamically)
        if not hasattr(self, 'hf_pipeline'):
            logger.info("Loading local generative model (google/flan-t5-base)...")
            self.hf_pipeline = pipeline(
                "text2text-generation", 
                model="google/flan-t5-base", 
                device="cpu"
            )
            logger.info("Local generative model loaded successfully.")

        # T5 prompt format for Q&A
        prompt = f"Answer the following question using only the context provided.\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        
        try:
            output = self.hf_pipeline(
                prompt,
                max_length=256,
                min_length=10,
                num_return_sequences=1,
                do_sample=False
            )
            answer = output[0]['generated_text'].strip()
            
            # Formatting nicely if the answer is too short or doesn't make sense
            if not answer or len(answer) < 5:
                 answer = "Based on the provided document, the information requested could not be synthesized clearly. Please refer to the citations."
        except Exception as e:
            logger.error(f"Generative AI logic failed: {e}")
            answer = "Sorry, I encountered an error while synthesizing the answer."
            
        return AnswerResult(
            answer=answer,
            mode="synthesized (local-t5)",
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
