"""
Phase 10: Confidence Gate
Deterministic gating module that decides whether retrieval results
are confident enough to proceed to the answer engine.

If the gate FAILS, the system refuses to answer with the exact phrase:
"This information is not present in the uploaded document."

No ML classifiers. No training. Pure threshold-based logic.
"""

import os
import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Exact refusal phrase — never change this
REFUSAL_PHRASE = "This information is not present in the uploaded document."

# Configurable thresholds via environment variables
DEFAULT_MIN_TOP_SCORE = 0.25       # minimum similarity for the best chunk
DEFAULT_MIN_AVG_SCORE = 0.15       # minimum average similarity across top-k
DEFAULT_MIN_LEXICAL_OVERLAP = 0.10 # minimum fraction of query terms found in top chunk
DEFAULT_MIN_CHUNKS_REQUIRED = 1    # at least N chunks must pass min_top_score


@dataclass
class GateResult:
    """Result of the confidence gate evaluation."""
    passed: bool
    confidence_score: float  # 0.0 to 1.0 composite score
    refusal_message: str | None = None
    diagnostics: dict = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """A single retrieval result with text and similarity."""
    text: str
    similarity: float
    document_id: int
    page_number: int
    chunk_index: int


class ConfidenceGate:
    """
    Deterministic confidence gate for retrieval-augmented QA.
    
    Evaluates retrieval results against configurable thresholds
    and decides whether to proceed to the answer engine or refuse.
    """
    
    def __init__(self):
        self.min_top_score = float(os.getenv("GATE_MIN_TOP_SCORE", DEFAULT_MIN_TOP_SCORE))
        self.min_avg_score = float(os.getenv("GATE_MIN_AVG_SCORE", DEFAULT_MIN_AVG_SCORE))
        self.min_lexical_overlap = float(os.getenv("GATE_MIN_LEXICAL_OVERLAP", DEFAULT_MIN_LEXICAL_OVERLAP))
        self.min_chunks_required = int(os.getenv("GATE_MIN_CHUNKS", DEFAULT_MIN_CHUNKS_REQUIRED))
        
        logger.info(
            f"ConfidenceGate initialized: top={self.min_top_score}, "
            f"avg={self.min_avg_score}, lexical={self.min_lexical_overlap}, "
            f"min_chunks={self.min_chunks_required}"
        )
    
    def evaluate(self, query: str, results: list[RetrievalResult]) -> GateResult:
        """
        Evaluate retrieval results against confidence thresholds.
        
        Returns a GateResult indicating whether to proceed or refuse.
        """
        diagnostics = {}
        
        # ---- Check 1: Do we have any results at all? ----
        if not results:
            diagnostics["reason"] = "no_results"
            diagnostics["detail"] = "Zero chunks retrieved"
            return GateResult(
                passed=False,
                confidence_score=0.0,
                refusal_message=REFUSAL_PHRASE,
                diagnostics=diagnostics
            )
        
        # ---- Compute metrics ----
        similarities = [r.similarity for r in results]
        top_score = max(similarities)
        avg_score = sum(similarities) / len(similarities)
        
        # Count how many chunks pass the minimum threshold
        passing_chunks = sum(1 for s in similarities if s >= self.min_top_score)
        
        # Lexical overlap: fraction of query terms found in the best chunk
        lexical_overlap = self._compute_lexical_overlap(query, results[0].text)
        
        diagnostics["top_score"] = round(top_score, 4)
        diagnostics["avg_score"] = round(avg_score, 4)
        diagnostics["lexical_overlap"] = round(lexical_overlap, 4)
        diagnostics["passing_chunks"] = passing_chunks
        diagnostics["total_chunks"] = len(results)
        diagnostics["thresholds"] = {
            "min_top_score": self.min_top_score,
            "min_avg_score": self.min_avg_score,
            "min_lexical_overlap": self.min_lexical_overlap,
            "min_chunks_required": self.min_chunks_required
        }
        
        # ---- Gate checks ----
        checks = {}
        
        # Check 2: Top score must meet minimum
        checks["top_score_ok"] = top_score >= self.min_top_score
        
        # Check 3: Average score must meet minimum
        checks["avg_score_ok"] = avg_score >= self.min_avg_score
        
        # Check 4: Lexical overlap must meet minimum
        checks["lexical_ok"] = lexical_overlap >= self.min_lexical_overlap
        
        # Check 5: Enough chunks must pass
        checks["enough_chunks"] = passing_chunks >= self.min_chunks_required
        
        diagnostics["checks"] = checks
        
        # ---- Decision: ALL checks must pass ----
        passed = all(checks.values())
        
        # Composite confidence score (weighted average of metrics)
        # This gives downstream consumers a single 0-1 score
        confidence_score = (
            0.50 * min(top_score / max(self.min_top_score, 0.01), 1.0) +
            0.30 * min(avg_score / max(self.min_avg_score, 0.01), 1.0) +
            0.20 * min(lexical_overlap / max(self.min_lexical_overlap, 0.01), 1.0)
        )
        confidence_score = max(0.0, min(confidence_score, 1.0))
        
        diagnostics["confidence_score"] = round(confidence_score, 4)
        
        if not passed:
            failed_checks = [k for k, v in checks.items() if not v]
            diagnostics["reason"] = "threshold_failure"
            diagnostics["failed_checks"] = failed_checks
            logger.info(f"Gate REFUSED query '{query[:50]}...' — failed: {failed_checks}")
            return GateResult(
                passed=False,
                confidence_score=confidence_score,
                refusal_message=REFUSAL_PHRASE,
                diagnostics=diagnostics
            )
        
        logger.info(
            f"Gate PASSED query '{query[:50]}...' — "
            f"confidence={confidence_score:.3f}, top={top_score:.3f}"
        )
        return GateResult(
            passed=True,
            confidence_score=confidence_score,
            refusal_message=None,
            diagnostics=diagnostics
        )
    
    def _compute_lexical_overlap(self, query: str, text: str) -> float:
        """
        Compute the fraction of unique query terms found in the text.
        
        Simple but effective: tokenize both, check membership.
        Ignores stopwords and very short tokens.
        """
        # Simple tokenization: lowercase, split on non-alphanumeric
        query_tokens = set(self._tokenize(query))
        text_tokens = set(self._tokenize(text))
        
        if not query_tokens:
            return 0.0
        
        overlap = query_tokens & text_tokens
        return len(overlap) / len(query_tokens)
    
    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase words, filtering short/stop words."""
        # Common English stopwords to ignore
        stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "and",
            "but", "or", "nor", "not", "so", "yet", "both", "either",
            "neither", "each", "every", "all", "any", "few", "more",
            "most", "other", "some", "such", "no", "only", "own", "same",
            "than", "too", "very", "just", "about", "above", "below",
            "between", "up", "down", "out", "off", "over", "under",
            "again", "further", "then", "once", "here", "there", "when",
            "where", "why", "how", "what", "which", "who", "whom",
            "this", "that", "these", "those", "it", "its", "i", "me",
            "my", "we", "our", "you", "your", "he", "him", "his", "she",
            "her", "they", "them", "their"
        }
        
        tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())
        return [t for t in tokens if len(t) > 2 and t not in stopwords]


# Singleton
confidence_gate = ConfidenceGate()
