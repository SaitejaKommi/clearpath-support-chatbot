# Written Answers

## Q1 — Routing Logic

**Rules:**
- Query length > 30 words → +1 (complex signal)
- Multiple questions (count of '?') > 1 → +2 (multi-part)
- Keywords like "how", "why", "troubleshoot" → +1
- Keywords like "error", "problem", "not working" → +1
- **Decision:** Score ≥ 3 = Complex, else Simple

**Why this boundary?**
I set the boundary at ≥3 so that no single weak signal classifies a query as complex. A long query alone does not always mean deep reasoning, and a single keyword like “how” can still be a simple lookup. By requiring multiple signals, the router better captures multi-step troubleshooting or ambiguous queries. This helps reserve the 70B model for reasoning-heavy cases while keeping greetings and factual lookups on the 8B model. The goal was balancing cost and quality without over-routing.

**Real misclassification example:**
Query: “Why is my dashboard not loading?”

It scored +2 (“why” and implied issue) but was routed to Simple. In some cases, it needed deeper troubleshooting steps, and 70B would have produced a more structured answer.

**How to improve without LLM:**
I would add:
Error-code detection (e.g., ERR_ patterns)
Domain-specific keywords like “SSO”, “API”, “webhook”
A rule: if >3 chunks retrieved → force Complex

---

## Q2 — Retrieval Failures

**Example failure:**
Query: "How do I set up SSO?"
Retrieved: [chunks about general authentication, not SSO specifically]
Why: The word "SSO" might not be in the docs, or docs use "Single Sign-On" instead.
Fix: Implement synonym expansion or semantic search.

The system retrieved chunks about general authentication and password policies, not the specific SSO configuration section. The failure happened because the documentation used the full term “Single Sign-On,” while the query used the abbreviation “SSO.” Since my retrieval relied mainly on embedding similarity without synonym handling, it matched broader authentication content instead.

This shows a weakness in handling abbreviations and terminology variations.

To fix this, I would implement synonym expansion before retrieval (e.g., map “SSO” → “Single Sign-On”) or add a lightweight keyword normalization layer. Another improvement would be hybrid search (keyword + vector search) to improve precision for technical terms.

---

## Q3 — Cost and Scale

**Scenario:** 5,000 queries/day

**Token estimation:**
- 70% simple queries (2,200 queries)
  - Avg 150 tokens in, 100 tokens out per query
  - = 2,200 × (150 + 100) = 550,000 tokens
- 30% complex queries (1,500 queries)
  - Avg 300 tokens in, 300 tokens out
  - = 1,500 × (300 + 300) = 900,000 tokens
- **Total: ~1.45M tokens/day**

**Cost driver:** Complex queries (62% of tokens, only 30% of queries)

**Highest-ROI optimization:** Better routing to reduce complex queries

Simple queries:
2,200 × (150 input + 100 output) = 550,000 tokens

Complex queries:
1,500 × (300 input + 300 output) = 900,000 tokens

Total ≈ 1.45M tokens/day

The biggest cost driver is complex queries. Even though they are only 30% of total traffic, they consume about 62% of total tokens. This is mainly due to larger context windows and longer reasoning outputs.

The highest-ROI optimization would be improving router precision so fewer borderline queries go to 70B unnecessarily. Even a 5–10% reduction in complex routing would significantly reduce token usage.

One optimization I would avoid is aggressively truncating retrieved context. That might reduce tokens but would hurt answer quality and increase hallucinations.

---

## Q4 — What Is Broken
Example: "The retriever doesn't handle typos or spelling mistakes. If a user types 'Cleerpath' or 'projct', retrieval fails completely."

The biggest limitation is that the retriever does not handle typos or spelling mistakes. If a user types “Cleerpath” or “projct settings,” retrieval may return irrelevant chunks or none at all. Since the LLM depends on retrieved context, this can lead to weak or hallucinated responses.

I shipped with this limitation because the core RAG + routing + evaluator pipeline was functioning correctly, and typo handling would require additional preprocessing or fuzzy search logic that was outside the time scope.

If I had more time, I would add a preprocessing layer with spelling correction or fuzzy keyword matching before retrieval. This would significantly improve robustness without changing the overall architecture.

