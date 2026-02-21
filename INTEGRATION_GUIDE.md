# Complete Backend Integration Guide

## What You Have

A fully functional AI chatbot backend with:

✅ **Query Router** (`router.py`)
- Classifies queries as simple or complex
- Routes to appropriate Groq model
- Logs all interactions

✅ **Document Retriever** (`retriever.py`)
- Loads extracted PDF chunks
- Finds relevant documents via similarity search
- Returns top-k most relevant chunks

✅ **LLM Caller** (`llm_caller.py`)
- Integrates with Groq API
- Builds context-aware prompts
- Tracks tokens and latency

✅ **Response Evaluator** (`evaluator.py`)
- Checks response reliability
- Detects hallucinations
- Provides confidence scores

✅ **Flask Server** (`app.py`)
- RESTful API endpoints
- CORS enabled for frontend
- Error handling and logging

## Setup Steps

### Step 1: Install Dependencies ✓ (Already Done)
```bash
pip install groq flask flask-cors python-dotenv PyPDF2 requests
```

### Step 2: Create .env File (IMPORTANT!)
Create file: `clearpath-support-chatbot/.env`
```
GROQ_API_KEY=gsk_YOUR_ACTUAL_API_KEY_HERE
```

**How to get your API key:**
1. Go to https://console.groq.com/keys
2. Sign in or create account (free)
3. Create API key
4. Copy and paste into .env file

### Step 3: Extract Documents (If You Have PDFs)
```bash
cd clearpath-support-chatbot

# Place your 30 PDF files in ./pdfs folder
# Then run:
python backend/pdf_processor.py
```

This creates: `./extracted_data/extracted_documents.json`

### Step 4: Start Backend
```bash
python backend/app.py
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

## Testing the Backend

### Test 1: Health Check
```bash
curl http://localhost:5000/health
```

### Test 2: Simple Query
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Clearpath?"}'
```

### Test 3: Complex Query
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I set up a new project and configure all advanced settings?"}'
```

### Test 4: Statistics
```bash
curl http://localhost:5000/stats
```

## Frontend Integration

### React Example

```jsx
import React, { useState } from 'react';

function ChatBot() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      const data = await res.json();
      setResponse(data);
      console.log('Tokens used:', data.tokens_input + data.tokens_output);
      console.log('Reliability:', data.is_reliable ? 'Yes' : 'No');
      console.log('Confidence:', data.confidence);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Loading...' : 'Send'}
        </button>
      </form>

      {response && (
        <div>
          <p><strong>Answer:</strong> {response.response}</p>
          <p><strong>Model:</strong> {response.model_used}</p>
          <p><strong>Confidence:</strong> {(response.confidence * 100).toFixed(0)}%</p>
          <p><strong>Reliable:</strong> {response.is_reliable ? '✓ Yes' : '✗ No'}</p>
        </div>
      )}
    </div>
  );
}

export default ChatBot;
```

### Vue Example

```vue
<template>
  <div class="chatbot">
    <form @submit.prevent="sendQuery">
      <input 
        v-model="query" 
        type="text" 
        placeholder="Ask a question..."
      />
      <button :disabled="loading">
        {{ loading ? 'Loading...' : 'Send' }}
      </button>
    </form>

    <div v-if="response" class="response">
      <p><strong>Answer:</strong> {{ response.response }}</p>
      <p><strong>Model:</strong> {{ response.model_used }}</p>
      <p><strong>Confidence:</strong> {{ Math.round(response.confidence * 100) }}%</p>
      <p><strong>Reliable:</strong> {{ response.is_reliable ? '✓ Yes' : '✗ No' }}</p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      query: '',
      response: null,
      loading: false,
    };
  },
  methods: {
    async sendQuery() {
      this.loading = true;
      try {
        const res = await fetch('http://localhost:5000/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: this.query }),
        });
        this.response = await res.json();
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
```

## Response Format

Every response from `/chat` includes:

```json
{
  "response": "The actual answer to the user's question",
  "model_used": "mixtral-8x7b-32768",  // or "llama-3.3-70b-versatile"
  "classification": "simple",  // or "complex"
  "is_reliable": true,
  "confidence": 0.92,  // 0.0 to 1.0
  "tokens_input": 145,
  "tokens_output": 218,
  "latency_ms": 1850,
  "total_latency_ms": 2100,
  "retrieved_chunks": 5,
  "evaluation_flags": {
    "no_context": false,
    "refusal": false,
    "hallucination": false
  },
  "debug_info": {
    "retrieved_sources": ["file1.pdf", "file2.pdf"],
    "retrieved_scores": [0.92, 0.87]
  }
}
```

## How It Works Behind the Scenes

### Request Flow

1. **User sends query via frontend**
   ```
   POST /chat
   {"query": "How do I create a project?"}
   ```

2. **Router classifies the query**
   - Analyzes: question count, length, keywords
   - Decides: simple (fast) or complex (powerful)
   - Simple: `mixtral-8x7b-32768` (~1-2 seconds)
   - Complex: `llama-3.3-70b-versatile` (~2-4 seconds)

3. **Retriever searches documents**
   - Loads all extracted PDF chunks
   - Calculates similarity to query
   - Returns top 5 most relevant chunks

4. **LLM Caller builds and sends prompt**
   ```
   System: "You are a support assistant..."
   User: "Question + relevant documentation"
   ```

5. **Groq API returns answer**
   - Returns generated response
   - Token counts (input/output)
   - Latency metrics

6. **Evaluator checks reliability**
   - No context check: Did we find relevant docs?
   - Refusal check: Did LLM refuse to answer?
   - Hallucination check: Is response too different from docs?
   - Confidence score: How trustworthy is the answer?

7. **Response sent to frontend**
   - Full response + metrics + quality flags

## Monitoring & Logs

All interactions are logged to `logs.jsonl`:

```json
{
  "timestamp": "2025-02-21T10:30:45.123456",
  "query": "How do I create a new...",
  "query_length": 35,
  "classification": "complex",
  "model_used": "llama-3.3-70b-versatile",
  "tokens_input": 210,
  "tokens_output": 320,
  "latency_ms": 2100,
  "response_reliable": true
}
```

View statistics:
```bash
curl http://localhost:5000/stats
```

Returns:
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

## Common Issues & Solutions

### "GROQ_API_KEY not set"
**Solution:** Add API key to `.env` file
```
GROQ_API_KEY=gsk_your_key_here
```

### "No documents found"
**Solutions:**
1. Create `./pdfs` folder with PDF files
2. Run: `python backend/pdf_processor.py`
3. Reload documents: `curl -X POST http://localhost:5000/documents/reload`

### "Module not found: groq"
**Solution:**
```bash
pip install groq
```

### "Connection refused" from frontend
**Solutions:**
- Backend running on `http://localhost:5000`?
- Frontend URL correct?
- CORS enabled? (Already in app.py)

### Slow responses
- **Simple queries** (~1-2 sec) - Expected
- **Complex queries** (~2-4 sec) - Expected
- Groq may queue requests during high load
- No custom optimization possible (API limitation)

## Performance Tips

1. **Cache responses** if asking same question multiple times
2. **Batch similar queries** to use same context
3. **Use simple model** for straightforward questions
4. **Monitor logs** to optimize your PDF content

## Next Steps

1. ✅ Backend is ready
2. Next: Build your frontend (React/Vue/Angular)
3. Then: Deploy both backend and frontend

## Support

For issues or questions:
- Check logs: `logs.jsonl`
- Run tests: `python test_backend.py`
- Check endpoint: `curl http://localhost:5000/health`

Good luck! 🚀
