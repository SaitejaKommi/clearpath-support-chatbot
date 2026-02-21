import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentRetriever:
    """Retrieves relevant document chunks based on query similarity."""
    
    def __init__(self, data_dir: str = "../extracted_data"):
        """
        Initialize retriever with extracted document data.
        
        Args:
            data_dir: Directory containing extracted JSON documents (default: ../extracted_data from backend)
        """
        self.data_dir = Path(data_dir)
        self.documents = []
        self.load_documents()
    
    def load_documents(self) -> None:
        """Load all extracted documents from JSON files."""
        if not self.data_dir.exists():
            logger.warning(f"Data directory not found: {self.data_dir}")
            return
        
        json_files = list(self.data_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle both single document and collection format
                    if isinstance(data, dict):
                        if "file" in data and "chunks" in data:
                            # Single document format
                            self.documents.append(data)
                        elif isinstance(next(iter(data.values()), None), dict):
                            # Collection format
                            for filename, doc_data in data.items():
                                self.documents.append(doc_data)
                    elif isinstance(data, list):
                        self.documents.extend(data)
            
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
        
        logger.info(f"Loaded {len(self.documents)} documents")
    
    def similarity_score(self, query: str, text: str) -> float:
        """
        Calculate similarity between query and text using word overlap.
        
        Args:
            query: User query
            text: Document text
            
        Returns:
            Similarity score between 0 and 1
        """
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words:
            return 0.0
        
        # Jaccard similarity
        intersection = len(query_words.intersection(text_words))
        union = len(query_words.union(text_words))
        
        return intersection / union if union > 0 else 0.0
    
    def retrieve_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve top-k most relevant chunks for a query.
        
        Args:
            query: User's question
            top_k: Number of chunks to retrieve
            
        Returns:
            List of relevant chunks with scores
        """
        if not self.documents:
            logger.warning("No documents loaded - returning empty results")
            return []
        
        scored_chunks = []
        
        # Score all chunks
        for doc in self.documents:
            filename = doc.get("file", "unknown")
            chunks = doc.get("chunks", [])
            
            for chunk in chunks:
                chunk_text = chunk.get("text", "")
                score = self.similarity_score(query, chunk_text)
                
                if score > 0:  # Only include chunks with some relevance
                    scored_chunks.append({
                        "text": chunk_text,
                        "page": chunk.get("page", 1),
                        "source": filename,
                        "chunk_id": chunk.get("id", 0),
                        "score": score,
                        "word_count": chunk.get("word_count", len(chunk_text.split()))
                    })
        
        # Sort by score and return top-k
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        top_chunks = scored_chunks[:top_k]
        
        logger.info(f"Retrieved {len(top_chunks)} chunks for query")
        
        return top_chunks


def retrieve_chunks(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function to retrieve chunks.
    
    Args:
        query: User's question
        top_k: Number of chunks to retrieve
        
    Returns:
        List of relevant chunks
    """
    retriever = DocumentRetriever()
    return retriever.retrieve_chunks(query, top_k=top_k)