#!/usr/bin/env python3
"""
Clearpath Support Chatbot - Main Flask Application
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

# ==========================================================
# ENV + LOGGING
# ==========================================================

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==========================================================
# FLASK INIT
# ==========================================================

app = Flask(__name__)
CORS(app)

@app.before_request
def log_requests():
    print("REQUEST:", request.method, request.path)

# ==========================================================
# GROQ CLIENT
# ==========================================================

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("❌ GROQ_API_KEY missing in .env")
    sys.exit(1)

client = Groq(api_key=groq_api_key)
logger.info("✓ Groq client initialized")

# ==========================================================
# ROUTER
# ==========================================================

class QueryRouter:
    def __init__(self):
        self.logs_file = Path("routing_logs.jsonl")

    def classify_query(self, query: str) -> str:
        score = 0
        q = query.lower()

        if query.count("?") > 1:
            score += 2

        if len(query.split()) > 25:
            score += 1

        reasoning = ["how", "why", "compare", "explain", "troubleshoot", "setup", "configure"]
        if any(word in q for word in reasoning):
            score += 1

        problems = ["error", "problem", "issue", "not working", "not loading", "failed", "fail", "bug"]
        if any(word in q for word in problems):
            score += 2

        logger.info(f"ROUTER SCORE: {score}")

        return "complex" if score >= 2 else "simple"

    def get_model(self, classification: str) -> str:
        return "llama-3.3-70b-versatile" if classification == "complex" else "llama-3.1-8b-instant"

    def log_query(self, data: dict):
        with open(self.logs_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

# ==========================================================
# RETRIEVER
# ==========================================================

class DocumentRetriever:
    def __init__(self, data_dir="./extracted_data"):
        self.data_dir = Path(data_dir)
        self.documents = []
        self.load_documents()

    def load_documents(self):
        if not self.data_dir.exists():
            logger.warning("No extracted_data folder found")
            return

        files = list(self.data_dir.glob("*_extracted.json"))
        for file in files:
            with open(file, "r", encoding="utf-8") as f:
                self.documents.append(json.load(f))

        logger.info(f"✓ Loaded {len(self.documents)} documents")

    def similarity_score(self, query, text):
        q_words = set(query.lower().split())
        t_words = set(text.lower().split())
        if not q_words:
            return 0
        return len(q_words & t_words) / len(q_words | t_words)

    def retrieve_chunks(self, query, top_k=5):
        results = []

        for doc in self.documents:
            for chunk in doc.get("chunks", []):
                score = self.similarity_score(query, chunk["text"])
                if score > 0:
                    results.append({
                        "text": chunk["text"],
                        "source": doc.get("file", "doc"),
                        "page": chunk.get("page", 1),
                        "score": score
                    })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

# ==========================================================
# EVALUATOR
# ==========================================================

class ResponseEvaluator:
    def check_no_context(self, chunks):
        return len(chunks) == 0

    def check_refusal(self, response):
        refusal = ["cannot", "don't know", "not available", "unable"]
        r = response.lower()
        return any(word in r for word in refusal)

    def check_hallucination(self, chunks, response):
        if not chunks:
            return False
        total_chunk_text = " ".join([c["text"] for c in chunks])
        return len(response) > 2 * len(total_chunk_text)

    def evaluate(self, chunks, response):
        flags = {
            "no_context": self.check_no_context(chunks),
            "refusal": self.check_refusal(response),
            "hallucination": self.check_hallucination(chunks, response)
        }
        reliable = not any(flags.values())
        return reliable, flags

# ==========================================================
# LLM CALLER
# ==========================================================

class LLMCaller:
    def __init__(self, client):
        self.client = client

    def build_prompt(self, query, chunks):
        context = "\n\n".join(
            [f"[{c['source']} p{c['page']}]\n{c['text']}" for c in chunks]
        ) or "No relevant documentation found."

        system = "You are a Clearpath support assistant. Answer only from documentation."
        user = f"Question: {query}\n\nDocumentation:\n{context}"

        return system, user

    def call(self, query: str, chunks: list, model_name: str):
        system_prompt, user_prompt = self.build_prompt(query, chunks)

        start_time = time.time()

        response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )

        latency_ms = int((time.time() - start_time) * 1000)

        response_text = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        return response_text, input_tokens, output_tokens, latency_ms

# ==========================================================
# INITIALIZE COMPONENTS
# ==========================================================

router = QueryRouter()
retriever = DocumentRetriever()
evaluator = ResponseEvaluator()
llm = LLMCaller(client)

# ==========================================================
# ROUTES
# ==========================================================

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "documents_loaded": len(retriever.documents)
    })

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"error": "Empty query"}), 400

        classification = router.classify_query(query)
        model = router.get_model(classification)

        chunks = retriever.retrieve_chunks(query)
        print("\n🔎 RETRIEVED CHUNKS:")
        for i, c in enumerate(chunks):
            print(f"\nChunk {i+1} | Source: {c.get('source')} | Score: {c.get('score')}")
            print(c.get("text")[:300])

        response_text, in_tokens, out_tokens, latency = llm.call(query, chunks, model)

        reliable, flags = evaluator.evaluate(chunks, response_text)

        router.log_query({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "classification": classification,
            "model_used": model,
            "tokens_input": in_tokens,
            "tokens_output": out_tokens,
            "latency_ms": latency,
            "reliable": reliable
        })

        return jsonify({
            "response": response_text,
            "model_used": model,
            "classification": classification,
            "tokens_input": in_tokens,
            "tokens_output": out_tokens,
            "latency_ms": latency,
            "is_reliable": reliable,
            "evaluation_flags": flags
        })

    except Exception as e:
        logger.exception("Chat endpoint failed")
        return jsonify({"error": str(e)}), 500

# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":
    print("🚀 Starting Clearpath Backend on http://localhost:5000")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)