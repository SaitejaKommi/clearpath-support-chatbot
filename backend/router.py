import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryRouter:
    """Routes queries to appropriate LLM model based on complexity."""
    
    def __init__(self, logs_file: str = "logs.jsonl"):
        """
        Initialize the router.
        
        Args:
            logs_file: Path to store classification logs
        """
        self.logs_file = Path(logs_file)
        self.logs_file.parent.mkdir(parents=True, exist_ok=True)
    
    def classify_query(self, query: str) -> str:
        """
        Classify a query as 'simple' or 'complex' based on heuristics.
        
        Args:
            query: The user's query
            
        Returns:
            'simple' or 'complex' classification
        """
        score = 0
        query_lower = query.lower()
        
        # Count questions - multiple questions indicate complexity
        question_count = query.count('?')
        if question_count > 1:
            score += 2
        
        # Check query length - longer queries tend to be more complex
        word_count = len(query.split())
        if word_count > 25:
            score += 1
        
        # Check for reasoning keywords
        reasoning_words = ['how', 'why', 'compare', 'explain', 'troubleshoot', 'design', 'architecture', 'setup', 'configure']
        if any(word in query_lower for word in reasoning_words):
            score += 1
        
        # Check for problem/error keywords
        complaint_words = ['not working', 'error', 'problem', 'issue', 'help', 'fail', 'bug']
        if any(word in query_lower for word in complaint_words):
            score += 1
        
        # Decision threshold: score >= 2 = complex, else simple
        classification = "complex" if score >= 2 else "simple"
        
        return classification
    
    def get_model_for_classification(self, classification: str) -> str:
        """
        Get the appropriate model name for the classification.
        
        Args:
            classification: 'simple' or 'complex'
            
        Returns:
            Model name to use
        """
        if classification == "complex":
            return "llama-3.3-70b-versatile"  # Powerful, slower model
        else:
            return "mixtral-8x7b-32768"  # Fast, smaller model
    
    def log_query_classification(self, 
                                query: str, 
                                classification: str, 
                                model_used: str,
                                tokens_input: int = None,
                                tokens_output: int = None,
                                latency_ms: int = None,
                                response_reliable: bool = None) -> None:
        """
        Log query classification and performance metrics.
        
        Args:
            query: The user's query
            classification: Classification result ('simple' or 'complex')
            model_used: Name of the model used
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens
            latency_ms: Response latency in milliseconds
            response_reliable: Whether the response was reliable
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:100],  # Log first 100 chars for privacy
            "query_length": len(query.split()),
            "classification": classification,
            "model_used": model_used,
        }
        
        # Add optional metrics
        if tokens_input is not None:
            log_entry["tokens_input"] = tokens_input
        if tokens_output is not None:
            log_entry["tokens_output"] = tokens_output
        if latency_ms is not None:
            log_entry["latency_ms"] = latency_ms
        if response_reliable is not None:
            log_entry["response_reliable"] = response_reliable
        
        # Append to JSONL file
        try:
            with open(self.logs_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
            logger.info(f"Logged query classification: {classification} -> {model_used}")
        except Exception as e:
            logger.error(f"Failed to log query classification: {e}")
    
    def get_logs_summary(self) -> dict:
        """
        Generate summary statistics from logs.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.logs_file.exists():
            return {"total_queries": 0, "summary": "No logs found"}
        
        simple_count = 0
        complex_count = 0
        total_latency = 0
        latency_count = 0
        reliable_count = 0
        total_count = 0
        
        try:
            with open(self.logs_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        total_count += 1
                        
                        if entry.get("classification") == "simple":
                            simple_count += 1
                        else:
                            complex_count += 1
                        
                        if entry.get("latency_ms"):
                            total_latency += entry["latency_ms"]
                            latency_count += 1
                        
                        if entry.get("response_reliable") is True:
                            reliable_count += 1
                    
                    except json.JSONDecodeError:
                        continue
            
            avg_latency = total_latency / latency_count if latency_count > 0 else 0
            
            return {
                "total_queries": total_count,
                "simple_queries": simple_count,
                "complex_queries": complex_count,
                "simple_percentage": (simple_count / total_count * 100) if total_count > 0 else 0,
                "complex_percentage": (complex_count / total_count * 100) if total_count > 0 else 0,
                "average_latency_ms": round(avg_latency, 2),
                "reliable_responses": reliable_count,
                "reliability_rate": (reliable_count / total_count * 100) if total_count > 0 else 0,
            }
        
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return {"error": str(e)}


def route_query(query: str) -> Tuple[str, str]:
    """
    Convenience function to classify a query and get the appropriate model.
    
    Args:
        query: The user's query
        
    Returns:
        Tuple of (classification, model_name)
    """
    router = QueryRouter()
    classification = router.classify_query(query)
    model = router.get_model_for_classification(classification)
    return classification, model


if __name__ == "__main__":
    # Test the router
    router = QueryRouter()
    
    test_queries = [
        "What is Clearpath?",
        "How do I set up a new project and what are the best practices for configuration and deployment?",
        "Error: module not found. How can I troubleshoot this issue?",
        "Tell me about your product.",
    ]
    
    print("="*60)
    print("QUERY ROUTER TEST")
    print("="*60)
    
    for query in test_queries:
        classification = router.classify_query(query)
        model = router.get_model_for_classification(classification)
        print(f"\nQuery: {query}")
        print(f"Classification: {classification}")
        print(f"Model: {model}")
        router.log_query_classification(query, classification, model)
    
    print("\n" + "="*60)
    print("LOGS SUMMARY")
    print("="*60)
    summary = router.get_logs_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
