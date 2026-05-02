"""
Phase 12: Support Validator
Post-generation validation that checks whether an answer is actually
grounded in the retrieved source chunks.

This is the LAST line of defense before an answer reaches the user.
If the answer contains claims not supported by the chunks, it gets
overridden with the exact refusal phrase.

Support levels:
- SUPPORTED: answer claims are found in source chunks
- PARTIALLY_SUPPORTED: some claims supported, some not
- UNSUPPORTED: answer claims are NOT found in source chunks

Conservative approach: refuse more than allow. Trust > convenience.
"""

import re
import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Same refusal phrase as confidence gate — consistency matters
REFUSAL_PHRASE = "This information is not present in the uploaded document."


class SupportLevel(str, Enum):
    supported = "supported"
    partially_supported = "partially_supported"
    unsupported = "unsupported"


@dataclass
class ValidationResult:
    """Result of the support validation."""
    level: SupportLevel
    original_answer: str
    validated_answer: str  # may be overridden with refusal
    coverage_score: float  # 0.0 to 1.0 — fraction of answer claims found in chunks
    supporting_chunk_indices: list[int] = field(default_factory=list)
    rejection_reasons: list[str] = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)


class SupportValidator:
    """
    Validates generated answers against source chunks.
    
    Strategy:
    1. Extract key claims/phrases from the answer
    2. Check each claim against the source chunks
    3. Compute coverage: what fraction of answer content is grounded
    4. If coverage is too low → override with refusal
    """
    
    # Minimum coverage threshold: at least this fraction of answer
    # content must be found in source chunks
    COVERAGE_THRESHOLD = 0.40  # 40% — conservative
    
    def validate(
        self,
        answer: str,
        chunks: list[dict],
        query: str
    ) -> ValidationResult:
        """
        Validate an answer against its source chunks.
        
        Args:
            answer: The generated answer text
            chunks: List of dicts with 'text', 'similarity', etc.
            query: The original query (for context)
        
        Returns:
            ValidationResult with support level and possibly overridden answer
        """
        diagnostics = {}
        rejection_reasons = []
        
        # Edge case: answer is already the refusal phrase
        if answer.strip() == REFUSAL_PHRASE:
            return ValidationResult(
                level=SupportLevel.supported,
                original_answer=answer,
                validated_answer=answer,
                coverage_score=1.0,
                supporting_chunk_indices=[],
                rejection_reasons=[],
                diagnostics={"note": "Answer is already a refusal"}
            )
        
        # Edge case: no chunks
        if not chunks:
            return ValidationResult(
                level=SupportLevel.unsupported,
                original_answer=answer,
                validated_answer=REFUSAL_PHRASE,
                coverage_score=0.0,
                supporting_chunk_indices=[],
                rejection_reasons=["No source chunks available"],
                diagnostics={}
            )
        
        # Step 1: Extract n-grams from the answer
        answer_ngrams = self._extract_ngrams(answer, n=3)
        answer_tokens = set(self._tokenize(answer))
        
        diagnostics["answer_ngram_count"] = len(answer_ngrams)
        diagnostics["answer_token_count"] = len(answer_tokens)
        
        # Step 2: Build combined source text and check coverage
        source_text = " ".join([c["text"] for c in chunks])
        source_tokens = set(self._tokenize(source_text))
        source_lower = source_text.lower()
        
        # Check n-gram coverage
        supported_ngrams = 0
        for ngram in answer_ngrams:
            if ngram.lower() in source_lower:
                supported_ngrams += 1
        
        ngram_coverage = supported_ngrams / max(len(answer_ngrams), 1)
        
        # Check token overlap
        if answer_tokens:
            token_overlap = len(answer_tokens & source_tokens) / len(answer_tokens)
        else:
            token_overlap = 0.0
        
        # Composite coverage (weighted)
        coverage = 0.6 * ngram_coverage + 0.4 * token_overlap
        
        diagnostics["ngram_coverage"] = round(ngram_coverage, 4)
        diagnostics["token_overlap"] = round(token_overlap, 4)
        diagnostics["composite_coverage"] = round(coverage, 4)
        diagnostics["threshold"] = self.COVERAGE_THRESHOLD
        
        # Step 3: Identify which chunks support the answer
        supporting_indices = []
        for i, chunk in enumerate(chunks):
            chunk_tokens = set(self._tokenize(chunk["text"]))
            chunk_overlap = len(answer_tokens & chunk_tokens)
            if chunk_overlap >= 3:  # at least 3 tokens shared
                supporting_indices.append(i)
        
        diagnostics["supporting_chunks"] = len(supporting_indices)
        diagnostics["total_chunks"] = len(chunks)
        
        # Step 4: Determine support level
        if coverage >= self.COVERAGE_THRESHOLD:
            if coverage >= 0.70:
                level = SupportLevel.supported
            else:
                level = SupportLevel.partially_supported
            validated_answer = answer
        else:
            level = SupportLevel.unsupported
            validated_answer = REFUSAL_PHRASE
            rejection_reasons.append(
                f"Coverage too low: {coverage:.2%} < {self.COVERAGE_THRESHOLD:.0%} threshold"
            )
            rejection_reasons.append(
                f"Only {supported_ngrams}/{len(answer_ngrams)} answer phrases found in source"
            )
            logger.warning(
                f"Support Validator REJECTED answer: coverage={coverage:.2%}, "
                f"ngram={ngram_coverage:.2%}, token={token_overlap:.2%}"
            )
        
        logger.info(
            f"Support Validator: level={level.value}, coverage={coverage:.2%}, "
            f"supporting_chunks={len(supporting_indices)}"
        )
        
        return ValidationResult(
            level=level,
            original_answer=answer,
            validated_answer=validated_answer,
            coverage_score=coverage,
            supporting_chunk_indices=supporting_indices,
            rejection_reasons=rejection_reasons,
            diagnostics=diagnostics
        )
    
    def _extract_ngrams(self, text: str, n: int = 3) -> list[str]:
        """Extract word n-grams from text for phrase-level matching."""
        words = text.lower().split()
        # Filter out very short words
        words = [w for w in words if len(w) > 1]
        
        if len(words) < n:
            return [" ".join(words)] if words else []
        
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = " ".join(words[i:i+n])
            ngrams.append(ngram)
        
        return ngrams
    
    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase content words."""
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


# Singleton
support_validator = SupportValidator()
