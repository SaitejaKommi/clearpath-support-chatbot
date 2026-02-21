# Backend Setup and Startup Guide

## Prerequisites

1. **Install dependencies** (already done):
```bash
pip install groq flask flask-cors python-dotenv PyPDF2 requests
```

2. **Set up .env file**:
```
GROQ_API_KEY=your_actual_groq_api_key_here
```

Get your API key from: https://console.groq.com/keys

## Project Structure

```
backend/
├── app.py                 # Main Flask application (START THIS)
├── router.py             # Query classification (simple vs complex)
├── retriever.py          # Document retrieval & similarity search
├── llm_caller.py         # Groq API integration
├── evaluator.py          # Response quality checks
├── pdf_processor.py      # PDF extraction (run once with your PDFs)
├── logs.jsonl            # Query logs (auto-created)
└── extracted_data/       # Extracted documents (created by pdf_processor.py)
```

## Quick Start

### Step 1: Extract Documents from PDFs

Place your 30 PDF files in a `./pdfs` directory, then:

```bash
cd backend
python pdf_processor.py
```

This creates `extracted_data/extracted_documents.json` with all chunks.

### Step 2: Start the Backend Server

```bash
cd backend
python app.py
```

You'll see:
```
Starting Clearpath Support Chatbot Backend...
Available endpoints:
  - POST /chat (main endpoint)
  - GET /health (health check)
  - GET /stats (statistics)
  - POST /documents/reload (reload documents)
 * Running on http://0.0.0.0:5000
```

### Step 3: Test the Backend

**Health Check:**
```bash
curl http://localhost:5000/health
```

**Send a Query:**
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I create a project?"}'
```

**Response Example:**
```json
{
  "response": "To create a project in Clearpath...",
  "model_used": "mixtral-8x7b-32768",
  "classification": "simple",
  "is_reliable": true,
  "confidence": 0.92,
  "tokens_input": 145,
  "tokens_output": 218,
  "latency_ms": 1850,
  "total_latency_ms": 2100,
  "retrieved_chunks": 5,
  "evaluation_flags": {
    "no_context": false,
    "refusal": false,
    "hallucination": false
  }
}
```

## API Endpoints

### POST /chat
Main endpoint for chatbot queries.

**Request:**
```json
{
  "query": "Your question here"
}
```

**Response:** See above example

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Clearpath Support Chatbot Backend is running"
}
```

### GET /stats
Get usage statistics.

**Response:**
```json
{
  "total_queries": 42,
  "simple_queries": 28,
  "complex_queries": 14,
  "simple_percentage": 66.67,
  "complex_percentage": 33.33,
  "average_latency_ms": 2150,
  "reliable_responses": 40,
  "reliability_rate": 95.24
}
```

### POST /documents/reload
Reload documents after running pdf_processor.py again.

**Response:**
```json
{
  "status": "success",
  "documents_loaded": 30
}
```

## How the Backend Works

### 1. Query Classification (router.py)
- Analyzes query complexity
- Routes to fast model (simple) or powerful model (complex)
- Logs all interactions

### 2. Document Retrieval (retriever.py)
- Loads extracted document chunks
- Calculates similarity to query
- Returns top 5 most relevant chunks

### 3. LLM Call (llm_caller.py)
- Builds context-aware prompt
- Calls Groq API
- Returns response + token counts + latency

### 4. Response Evaluation (evaluator.py)
- Checks if response is reliable
- Detects: no context, refusal, hallucination
- Provides confidence score (0-1)

## Frontend Integration

**Connect from your React/Vue/Angular app:**

```javascript
// JavaScript example
async function askChatbot(question) {
  const response = await fetch('http://localhost:5000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query: question })
  });
  
  const data = await response.json();
  return data;
}
```

**Make sure CORS is enabled** (already configured in app.py with flask-cors).

## Troubleshooting

**"GROQ_API_KEY not set"**
- Add your API key to `.env` file
- Ensure .env is in the root project directory

**"No documents found"**
- Run `pdf_processor.py` with PDFs in `./pdfs` folder
- Check that `extracted_data/` folder is created
- Run `POST /documents/reload` endpoint

**"ImportError: No module named 'groq'"**
```bash
pip install groq
```

**"ImportError: No module named 'flask'"**
```bash
pip install flask flask-cors
```

## Architecture Diagram

```
User Query (Frontend)
    ↓
[Router] - Classify complexity
    ↓
[Retriever] - Find relevant docs
    ↓
[LLM Caller] - Call Groq API
    ↓
[Evaluator] - Check reliability
    ↓
Response to Frontend
```

## Performance Notes

- Simple queries: ~1-2 seconds (smaller model)
- Complex queries: ~2-4 seconds (larger model)
- Latency depends on network and model queue times
- Confidence scores indicate response reliability

Enjoy! 🚀
