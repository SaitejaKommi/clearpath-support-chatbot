import os
import time
import logging
from typing import List, Dict, Tuple, Any
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    print("Warning: Groq SDK not installed. Install with: pip install groq")
    Groq = None

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMCaller:
    """Calls Groq LLM API with chunk context for question answering."""

    def __init__(self, api_key: str = None):
        """
        Initialize LLM caller.

        Args:
            api_key: Groq API key (uses GROQ_API_KEY env var if not provided)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        if Groq is None:
            raise ImportError("Groq SDK not installed. Install with: pip install groq")

        self.client = Groq(api_key=self.api_key)
        logger.info("LLM Caller initialized")

    def build_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> Tuple[str, str]:
        """
        Build a prompt combining the query and retrieved chunks.

        Args:
            query: User's question
            chunks: List of relevant document chunks

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Extract text from chunks
        chunk_texts = []
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get("text", "")
            source = chunk.get("source", "document")
            page = chunk.get("page", "unknown")

            chunk_texts.append(f"[Chunk {i} - {source} (page {page})]\n{text}")

        chunks_as_text = "\n\n".join(chunk_texts)

        system_prompt = """You are a helpful support assistant for Clearpath. 
Your role is to answer user questions accurately and helpfully based on the provided documentation.

Guidelines:
- Answer only based on the documentation provided
- Be concise and clear
- If the documentation doesn't contain the answer, say so explicitly
- Provide relevant page/section references when helpful
- Be professional and friendly"""

        user_prompt = f"""User Question: {query}

Relevant Documentation:
{chunks_as_text}

Please answer the question based on the documentation above."""

        return system_prompt, user_prompt

    def call_llm(
        self, query: str, chunks: list, model_name: str, max_tokens: int = 500
    ) -> Tuple[str, int, int, int]:
        """
        Call the Groq LLM with document context.

        Returns:
            response_text, input_tokens, output_tokens, latency_ms
        """
        system_prompt, user_prompt = self.build_prompt(query, chunks)
        start_time = time.time()

        response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # Extract response and token usage
        response_text = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        logger.info(
            f"✓ LLM call successful - {model_name} - "
            f"{input_tokens} in, {output_tokens} out, {latency_ms}ms"
        )

        return response_text, input_tokens, output_tokens, latency_ms

    def call_llm_simple(self, query: str, model_name: str) -> str:
        """
        Call LLM without document context (fallback).

        Args:
            query: User's question
            model_name: Name of Groq model to use

        Returns:
            Response text
        """
        try:
            response = self.client.messages.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
                max_tokens=500,
                temperature=0.3,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise


def call_llm_with_routing(
    query: str, chunks: List[Dict[str, Any]], classification: str = None
) -> Tuple[str, str, int, int, int]:
    """
    High-level function to call LLM with automatic model selection.

    Args:
        query: User's question
        chunks: List of relevant document chunks
        classification: 'simple' or 'complex' (auto-detect if not provided)

    Returns:
        Tuple of (response, model_used, input_tokens, output_tokens, latency_ms)
    """
    # Determine model based on classification
    if classification == "complex":
        model = "llama-3.3-70b-versatile"
    else:
        model = "mixtral-8x7b-32768"

    # Initialize caller and make request
    caller = LLMCaller()
    response, input_tokens, output_tokens, latency_ms = caller.call_llm(
        query=query, chunks=chunks, model_name=model
    )

    return response, model, input_tokens, output_tokens, latency_ms


if __name__ == "__main__":
    # Test LLM caller with sample chunks
    sample_chunks = [
        {
            "text": "Clearpath is a project management and collaboration platform designed for teams. "
            "It provides tools for task tracking, file sharing, and team communication.",
            "source": "getting_started.pdf",
            "page": 1,
        },
        {
            "text": "To create a new project in Clearpath, navigate to the Dashboard and click 'New Project'. "
            "Fill in the project name, description, and team members.",
            "source": "user_guide.pdf",
            "page": 5,
        },
    ]

    test_query = "How do I create a new project in Clearpath?"

    print("=" * 60)
    print("LLM CALLER TEST")
    print("=" * 60)
    print(f"\nQuery: {test_query}")
    print(f"Chunks provided: {len(sample_chunks)}")

    try:
        caller = LLMCaller()
        response, input_tokens, output_tokens, latency_ms = caller.call_llm(
            query=test_query, chunks=sample_chunks, model_name="mixtral-8x7b-32768"
        )

        print("\n" + "=" * 60)
        print("RESPONSE")
        print("=" * 60)
        print(response)
        print("\n" + "=" * 60)
        print("METRICS")
        print("=" * 60)
        print(f"Input Tokens: {input_tokens}")
        print(f"Output Tokens: {output_tokens}")
        print(f"Latency: {latency_ms}ms")

    except ValueError as e:
        print(f"Error: {e}")
        print("\nMake sure GROQ_API_KEY is set in .env file")
    except Exception as e:
        print(f"Error: {e}")