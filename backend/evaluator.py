import logging
from typing import List, Dict, Tuple, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResponseEvaluator:
    """Evaluates LLM responses for reliability and trustworthiness."""
    
    def __init__(self, hallucination_ratio_threshold: float = 2.0):
        """
        Initialize response evaluator.
        
        Args:
            hallucination_ratio_threshold: Response length can be at most this ratio 
                                          of chunk text length before flagging as suspicious
        """
        self.hallucination_ratio_threshold = hallucination_ratio_threshold
    
    def check_no_context(self, retrieved_chunks: List[Dict[str, Any]]) -> bool:
        """
        Check if no relevant chunks were retrieved.
        
        Args:
            retrieved_chunks: List of retrieved document chunks
            
        Returns:
            True if no context was found (unreliable), False otherwise
        """
        if len(retrieved_chunks) == 0:
            logger.warning("No context retrieved - response may be unreliable")
            return True
        return False
    
    def check_refusal(self, llm_response: str) -> bool:
        """
        Check if the LLM refused to answer.
        
        Args:
            llm_response: Response from LLM
            
        Returns:
            True if refusal detected (unreliable), False otherwise
        """
        refusal_keywords = [
            'cannot help',
            "don't know",
            'no information',
            'not available',
            'cannot answer',
            'unable to answer',
            'no data',
            'not found',
            'i cannot',
            "i can't",
            'not mentioned',
            'outside the scope',
            'beyond my knowledge'
        ]
        
        response_lower = llm_response.lower()
        
        for keyword in refusal_keywords:
            if keyword in response_lower:
                logger.warning(f"Refusal detected: '{keyword}' found in response")
                return True
        
        return False
    
    def check_hallucination(self, 
                           retrieved_chunks: List[Dict[str, Any]], 
                           llm_response: str) -> bool:
        """
        Check if the LLM might be hallucinating (inventing facts).
        
        Uses multiple heuristics:
        1. Response length compared to chunk length
        2. Presence of specific claims without context
        3. Contradictions with source material
        
        Args:
            retrieved_chunks: List of retrieved document chunks
            llm_response: Response from LLM
            
        Returns:
            True if hallucination suspected (unreliable), False otherwise
        """
        if not retrieved_chunks:
            return False
        
        # Get total chunk text length
        chunk_text = " ".join([c.get("text", "") for c in retrieved_chunks])
        chunk_length = len(chunk_text)
        response_length = len(llm_response)
        
        # Heuristic 1: If response is much longer than all chunks combined,
        # it might be adding information not in the source
        length_ratio = response_length / chunk_length if chunk_length > 0 else 0
        
        if length_ratio > self.hallucination_ratio_threshold:
            logger.warning(
                f"Possible hallucination: Response length ({response_length}) is "
                f"{length_ratio:.1f}x the chunk length ({chunk_length})"
            )
            return True
        
        # Heuristic 2: Check for vague claims without specifics
        vague_phrases = [
            "it is known that",
            "everyone knows",
            "as we all know",
            "obviously",
            "clearly",
            "of course",
            "needless to say"
        ]
        
        response_lower = llm_response.lower()
        for phrase in vague_phrases:
            if phrase in response_lower:
                # Vague language combined with confident tone is suspicious
                logger.warning(f"Suspicious vague language detected: '{phrase}'")
                return True
        
        # Heuristic 3: Check if specific product features/versions are mentioned
        # that don't appear in chunks
        chunk_lower = chunk_text.lower()
        
        # Look for version numbers or specific features
        import re
        version_pattern = r'v?\d+\.\d+(?:\.\d+)?'
        response_versions = set(re.findall(version_pattern, response_lower))
        chunk_versions = set(re.findall(version_pattern, chunk_lower))
        
        # If response mentions versions not in chunks, flag it
        if response_versions and not response_versions.intersection(chunk_versions):
            logger.warning(
                f"Version mismatch: Response mentions {response_versions} "
                f"but chunks only mention {chunk_versions}"
            )
            return True
        
        return False
    
    def evaluate_response(self, 
                         query: str,
                         retrieved_chunks: List[Dict[str, Any]], 
                         llm_response: str) -> Tuple[bool, Dict[str, bool]]:
        """
        Evaluate overall response reliability by running all checks.
        
        Args:
            query: Original user query
            retrieved_chunks: List of retrieved document chunks
            llm_response: Response from LLM
            
        Returns:
            Tuple of (is_reliable, flags_dict)
            - is_reliable: True if response passes all checks
            - flags_dict: Dictionary showing which checks failed
        """
        flags = {
            "no_context": self.check_no_context(retrieved_chunks),
            "refusal": self.check_refusal(llm_response),
            "hallucination": self.check_hallucination(retrieved_chunks, llm_response)
        }
        
        # Response is reliable if no flags are raised
        is_reliable = not any(flags.values())
        
        if is_reliable:
            logger.info("Response evaluation: RELIABLE")
        else:
            failed_checks = [k for k, v in flags.items() if v]
            logger.warning(f"Response evaluation: UNRELIABLE - Failed checks: {failed_checks}")
        
        return is_reliable, flags
    
    def get_confidence_score(self, 
                            retrieved_chunks: List[Dict[str, Any]], 
                            llm_response: str) -> float:
        """
        Calculate a confidence score (0.0 to 1.0) for the response.
        
        Args:
            retrieved_chunks: List of retrieved document chunks
            llm_response: Response from LLM
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 1.0
        
        # Deduct points for various risk factors
        if self.check_no_context(retrieved_chunks):
            score -= 0.5
        
        if self.check_refusal(llm_response):
            score -= 0.3
        
        if self.check_hallucination(retrieved_chunks, llm_response):
            score -= 0.4
        
        # Bonus points if we have good context
        if len(retrieved_chunks) >= 3:
            score += 0.1
        
        # Return score clamped between 0 and 1
        return max(0.0, min(1.0, score))


def evaluate_and_handle(query: str,
                       retrieved_chunks: List[Dict[str, Any]],
                       llm_response: str,
                       fallback_message: str = None) -> Tuple[str, bool, Dict[str, Any]]:
    """
    High-level function to evaluate response and optionally show fallback.
    
    Args:
        query: Original user query
        retrieved_chunks: List of retrieved document chunks
        llm_response: Response from LLM
        fallback_message: Message to show if response is unreliable
        
    Returns:
        Tuple of (final_response, is_reliable, evaluation_details)
    """
    evaluator = ResponseEvaluator()
    is_reliable, flags = evaluator.evaluate_response(query, retrieved_chunks, llm_response)
    confidence = evaluator.get_confidence_score(retrieved_chunks, llm_response)
    
    evaluation_details = {
        "is_reliable": is_reliable,
        "confidence_score": confidence,
        "flags": flags,
        "chunks_retrieved": len(retrieved_chunks)
    }
    
    # If unreliable and fallback provided, use it
    if not is_reliable and fallback_message:
        final_response = fallback_message
    else:
        final_response = llm_response
    
    return final_response, is_reliable, evaluation_details


if __name__ == "__main__":
    # Test the evaluator with different scenarios
    evaluator = ResponseEvaluator()
    
    # Test Case 1: Good response
    print("="*60)
    print("TEST CASE 1: Good Response with Context")
    print("="*60)
    good_chunks = [
        {"text": "Clearpath is a project management platform for teams."},
        {"text": "To create a project, click 'New Project' on the dashboard."}
    ]
    good_response = "To create a project in Clearpath, simply click the 'New Project' button on the dashboard."
    
    is_reliable, flags = evaluator.evaluate_response("How to create a project?", good_chunks, good_response)
    confidence = evaluator.get_confidence_score(good_chunks, good_response)
    print(f"Reliable: {is_reliable}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Flags: {flags}\n")
    
    # Test Case 2: No context
    print("="*60)
    print("TEST CASE 2: No Context Retrieved")
    print("="*60)
    empty_chunks = []
    response = "Based on Clearpath documentation..."
    
    is_reliable, flags = evaluator.evaluate_response("Complex question?", empty_chunks, response)
    confidence = evaluator.get_confidence_score(empty_chunks, response)
    print(f"Reliable: {is_reliable}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Flags: {flags}\n")
    
    # Test Case 3: Refusal
    print("="*60)
    print("TEST CASE 3: LLM Refusal")
    print("="*60)
    chunks = [{"text": "Some documentation"}]
    refusal_response = "I cannot find information about that in the documentation."
    
    is_reliable, flags = evaluator.evaluate_response("Question?", chunks, refusal_response)
    confidence = evaluator.get_confidence_score(chunks, refusal_response)
    print(f"Reliable: {is_reliable}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Flags: {flags}\n")
    
    # Test Case 4: Possible hallucination
    print("="*60)
    print("TEST CASE 4: Possible Hallucination (Too Long)")
    print("="*60)
    short_chunks = [{"text": "Short text."}]
    long_response = "This is a very long response " * 50  # Artificially long
    
    is_reliable, flags = evaluator.evaluate_response("Question?", short_chunks, long_response)
    confidence = evaluator.get_confidence_score(short_chunks, long_response)
    print(f"Reliable: {is_reliable}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Flags: {flags}")
