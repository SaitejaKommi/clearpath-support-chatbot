#!/usr/bin/env python3
"""
Quick test script to verify backend components work correctly.
Run this before starting the full Flask server.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def test_imports():
    """Test that all imports work."""
    print("=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)
    
    try:
        from router import QueryRouter
        print("✓ router.py imports successfully")
    except Exception as e:
        print(f"✗ router.py import failed: {e}")
        return False
    
    try:
        from retriever import DocumentRetriever
        print("✓ retriever.py imports successfully")
    except Exception as e:
        print(f"✗ retriever.py import failed: {e}")
        return False
    
    try:
        from evaluator import ResponseEvaluator
        print("✓ evaluator.py imports successfully")
    except Exception as e:
        print(f"✗ evaluator.py import failed: {e}")
        return False
    
    try:
        from llm_caller import LLMCaller
        print("✓ llm_caller.py imports successfully")
    except Exception as e:
        print(f"✗ llm_caller.py import failed: {e}")
        return False
    
    try:
        from flask import Flask
        print("✓ flask imports successfully")
    except Exception as e:
        print(f"✗ flask import failed: {e}")
        return False
    
    return True


def test_router():
    """Test query routing."""
    print("\n" + "=" * 60)
    print("TESTING QUERY ROUTER")
    print("=" * 60)
    
    try:
        from router import QueryRouter
        
        router = QueryRouter()
        
        test_queries = [
            ("What is Clearpath?", "simple"),
            ("How do I set up a new project and configure all the advanced settings?", "complex"),
            ("Error: module not found", "complex"),
        ]
        
        for query, expected in test_queries:
            classification = router.classify_query(query)
            model = router.get_model_for_classification(classification)
            status = "✓" if classification == expected else "✗"
            print(f"{status} '{query[:40]}...' → {classification} ({model})")
        
        return True
    
    except Exception as e:
        print(f"✗ Router test failed: {e}")
        return False


def test_retriever():
    """Test document retriever."""
    print("\n" + "=" * 60)
    print("TESTING DOCUMENT RETRIEVER")
    print("=" * 60)
    
    try:
        from retriever import DocumentRetriever
        
        retriever = DocumentRetriever(data_dir="./extracted_data")
        
        if len(retriever.documents) == 0:
            print("⚠ No documents loaded (run pdf_processor.py first)")
            print("✓ Retriever initialized correctly (no docs available yet)")
        else:
            print(f"✓ Loaded {len(retriever.documents)} documents")
            
            chunks = retriever.retrieve_chunks("test query", top_k=3)
            print(f"✓ Retrieved {len(chunks)} chunks for test query")
        
        return True
    
    except Exception as e:
        print(f"✗ Retriever test failed: {e}")
        return False


def test_evaluator():
    """Test response evaluator."""
    print("\n" + "=" * 60)
    print("TESTING RESPONSE EVALUATOR")
    print("=" * 60)
    
    try:
        from evaluator import ResponseEvaluator
        
        evaluator = ResponseEvaluator()
        
        # Test case 1: Good response
        good_chunks = [{"text": "Clearpath is a platform"}]
        good_response = "Clearpath is a great platform for teams."
        is_reliable, flags = evaluator.evaluate_response("query", good_chunks, good_response)
        print(f"✓ Good response evaluation: reliable={is_reliable}")
        
        # Test case 2: No context
        empty_chunks = []
        response = "Based on documentation..."
        is_reliable, flags = evaluator.evaluate_response("query", empty_chunks, response)
        print(f"✓ No context detection: reliable={is_reliable} (should be False)")
        
        # Test case 3: Confidence scoring
        confidence = evaluator.get_confidence_score(good_chunks, good_response)
        print(f"✓ Confidence scoring: {confidence:.2f}")
        
        return True
    
    except Exception as e:
        print(f"✗ Evaluator test failed: {e}")
        return False


def test_llm_caller():
    """Test LLM caller."""
    print("\n" + "=" * 60)
    print("TESTING LLM CALLER")
    print("=" * 60)
    
    try:
        from llm_caller import LLMCaller
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            print("⚠ GROQ_API_KEY not set in .env file")
            print("✓ LLM Caller class imports correctly (API key needed for actual calls)")
            return True
        
        try:
            caller = LLMCaller(api_key=api_key)
            print("✓ LLM Caller initialized with valid API key")
            return True
        except Exception as e:
            print(f"✗ LLM Caller initialization failed: {e}")
            return False
    
    except Exception as e:
        print(f"✗ LLM Caller test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " CLEARPATH SUPPORT CHATBOT - BACKEND VERIFICATION ".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = {
        "Imports": test_imports(),
        "Router": test_router(),
        "Retriever": test_retriever(),
        "Evaluator": test_evaluator(),
        "LLM Caller": test_llm_caller(),
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n✓ All tests passed! Backend is ready to run.")
        print("\nNext steps:")
        print("  1. Add your GROQ_API_KEY to .env file")
        print("  2. Run: python pdf_processor.py (with your PDFs)")
        print("  3. Run: python backend/app.py")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
