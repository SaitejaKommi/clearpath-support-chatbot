# Clearpath Support Chatbot

A production-ready AI-powered support chatbot that:
- **Extracts** text from 30+ PDF documents
- **Routes** queries based on complexity (simple vs. complex)
- **Retrieves** relevant documentation chunks
- **Calls** Groq LLM API for intelligent responses
- **Evaluates** response quality and reliability

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Your Groq API Key
Create a `.env` file:
```
GROQ_API_KEY=your_api_key_here
```

Get your key at: https://console.groq.com/keys

### 3. Extract PDFs (First Time Only)
Place your PDF files in a `./pdfs` folder, then:
```bash
python backend/pdf_processor.py
```

### 4. Start the Backend
```bash
python backend/app.py
```

Server will run at `http://localhost:5000`

## API Endpoints

### POST /chat
Send a query and get an answer.

**Request:**
```json
{
  "query": "How do I create a project?"
}
```

**Response:**
```json
{
  "response": "To create a project...",
  "model_used": "mixtral-8x7b-32768",
  "classification": "simple",
  "is_reliable": true,
  "confidence": 0.92,
  "tokens_input": 145,
  "tokens_output": 218,
  "latency_ms": 1850,
  "retrieved_chunks": 5
}
```

### GET /health
Health check.

### GET /stats
Usage statistics.

### POST /documents/reload
Reload documents after adding new PDFs.

## Architecture

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

## Key Features

- **Smart Routing**: Routes simple queries to fast model, complex to powerful model
- **Document Retrieval**: Semantic search through extracted chunks
- **Response Evaluation**: Detects hallucinations, refusals, and missing context
- **Logging**: Tracks all queries and performance metrics
- **CORS Support**: Works seamlessly with React/Vue/Angular frontends

## Directory Structure

```
clearpath-support-chatbot/
├── backend/
│   ├── app.py              # Flask server (main entry point)
│   ├── router.py           # Query classification
│   ├── retriever.py        # Document search
│   ├── llm_caller.py       # Groq API integration
│   ├── evaluator.py        # Response quality checks
│   ├── pdf_processor.py    # PDF extraction
│   └── logs.jsonl          # Query logs
├── frontend/               # React/Vue app goes here
├── docs/                   # Documentation
├── test_backend.py         # Verification tests
├── start_backend.bat       # Windows startup script
├── .env                    # Configuration (not in git)
└── requirements.txt        # Python dependencies
```

## Testing

Verify everything works:
```bash
python test_backend.py
```

## Troubleshooting

**No documents found?**
```bash
python backend/pdf_processor.py  # Run with PDFs in ./pdfs folder
```

**API Key error?**
- Check `.env` has `GROQ_API_KEY=your_key`
- Get key from https://console.groq.com/keys

**Import errors?**
```bash
pip install -r requirements.txt
```

## Frontend Integration

From your React/Vue/Angular app:

```javascript
const response = await fetch('http://localhost:5000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'Your question' })
});

const data = await response.json();
console.log(data.response);
```

## Documentation

- [Backend Setup Guide](./BACKEND_SETUP.md) - Detailed setup and API documentation
- [PDF Processing](./backend/pdf_processor.py) - Document extraction pipeline
- [Query Routing](./backend/router.py) - Classification logic
- [Response Evaluation](./backend/evaluator.py) - Quality checks

## License

All rights reserved.

SAITEJA
