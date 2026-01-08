# AI Intelligence Endpoints - API Reference

## Overview
New LLM-powered endpoints for intelligent workflow generation, prediction, and learning.

All endpoints use `use_ai=true` by default and integrate with Groq LLM.

---

## 1. Get Workflow Alternatives
**Endpoint:** `POST /api/agents/{agent_name}/alternatives`

**Purpose:** Generate multiple workflow approaches with trade-offs

**Request:**
```json
{
  "request": "send emails to tech companies"
}
```

**Response:**
```json
{
  "agent_name": "sales",
  "request": "send emails to tech companies",
  "alternatives": [
    {
      "name": "Email Blast Approach",
      "steps": [...],
      "pros": ["Fast", "Reaches many people"],
      "cons": ["Lower personalization"],
      "estimated_time": 30
    },
    {
      "name": "Personalized Outreach",
      "steps": [...],
      "pros": ["High engagement", "Personalized"],
      "cons": ["Takes longer"],
      "estimated_time": 120
    }
  ],
  "count": 2
}
```

---

## 2. Predict Workflow Success
**Endpoint:** `POST /api/agents/{agent_name}/predict`

**Purpose:** Predict success probability before execution

**Request:**
```json
{
  "request": "send emails to tech companies"
}
```

**Response:**
```json
{
  "agent_name": "sales",
  "request": "send emails to tech companies",
  "prediction": {
    "probability": 0.85,
    "reasoning": "Similar workflows have 85% success rate based on user history",
    "risk_factors": ["Email deliverability", "Response rate variability"],
    "estimated_duration": 60
  },
  "success_probability": 0.85,
  "risk_factors": ["Email deliverability", "Response rate variability"]
}
```

---

## 3. Learn from Execution
**Endpoint:** `POST /api/workflows/{plan_id}/learn`

**Purpose:** Extract insights and improve future workflows

**Request:**
```json
{
  "feedback": "workflow worked well but took too long",
  "rating": 4
}
```

**Response:**
```json
{
  "plan_id": "uuid-xxx",
  "learning": {
    "patterns": ["email_first_then_linkedin", "personalization_increases_response"],
    "improvements": ["Reduce email validation step", "Parallelize email sending"],
    "confidence": 0.92
  },
  "patterns_extracted": [
    "email_first_then_linkedin",
    "personalization_increases_response"
  ],
  "improvements": [
    "Reduce email validation step",
    "Parallelize email sending"
  ],
  "message": "Learning stored and will improve future workflows"
}
```

---

## 4. Get Workflow Insights
**Endpoint:** `GET /api/workflows/insights?limit=10`

**Purpose:** Get AI analysis of user's workflow patterns and recommendations

**Query Parameters:**
- `limit` (optional, default=10): Number of workflows to analyze

**Response:**
```json
{
  "total_workflows": 25,
  "agents_used": {
    "sales": 12,
    "marketing": 8,
    "finance": 5
  },
  "success_rate": "92.0%",
  "avg_steps_per_workflow": 3.2,
  "recommendations": [
    "Workflows are being used most often with: sales",
    "Consider automating recurring finance tasks",
    "Email workflows show highest success rate"
  ]
}
```

---

## Authentication
Add header: `X-User-ID: your-user-id`

---

## Integration with Execute Endpoint

The main `/api/agents/{agent_name}/execute` endpoint now supports AI:

**Request:**
```json
{
  "request": "send emails to tech companies",
  "auto_execute": true
}
```

**Response includes:**
```json
{
  "ai_powered": true,
  "ai_confidence": 0.88,
  "ai_reasoning": "Generating workflow based on similar past requests",
  "success_probability": 0.85,
  "alternatives": [...],
  "estimated_time": 60,
  "learning": {
    "patterns": [...],
    "improvements": [...]
  }
}
```

---

## How It Works

### 1. Intelligent Generation
- Analyzes user request with full context
- Pulls user history (past 10-20 workflows)
- Extracts patterns and preferences
- Generates optimal workflow

### 2. Alternative Generation
- Always creates 2-3 different approaches
- Shows trade-offs (speed vs accuracy, cost vs features)
- User can choose best option

### 3. Success Prediction
- Analyzes workflow complexity
- Checks historical patterns
- Predicts probability (0-1)
- Identifies risk factors

### 4. Learning System
- After execution: LLM analyzes results
- Extracts improvement suggestions
- Stores successful patterns
- Applies learning to future workflows

---

## Caching
- In-memory cache: 1 hour TTL
- Deduplicates identical requests
- Reduces LLM API calls
- Improves response time

---

## Error Handling

All endpoints return consistent error format:

```json
{
  "error": "Description of what went wrong"
}
```

Common errors:
- `Agent 'xyz' not found` (404)
- `Missing 'request' field` (400)
- `Workflow xyz not found` (404)

---

## Usage Examples

### Example 1: Get Alternatives
```bash
curl -X POST http://localhost:5000/api/agents/sales/alternatives \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user-123" \
  -d '{"request": "reach out to finance directors"}'
```

### Example 2: Predict Success
```bash
curl -X POST http://localhost:5000/api/agents/marketing/predict \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user-123" \
  -d '{"request": "create email campaign for Q1"}'
```

### Example 3: Learn from Execution
```bash
curl -X POST http://localhost:5000/api/workflows/plan-123/learn \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user-123" \
  -d '{
    "feedback": "worked great, response rate was 25%",
    "rating": 5
  }'
```

### Example 4: Get Insights
```bash
curl http://localhost:5000/api/workflows/insights?limit=20 \
  -H "X-User-ID: user-123"
```

---

## Architecture

```
Request
   ↓
Agent Engine (agent_engine.py)
   ↓
Base Agent + LLM Methods
   ↓
AI Intelligence Layer (agent_intelligence.py)
   ↓
Groq LLM (mixtral-8x7b-instruct-v0.1)
   ↓
Provider Registry (200+ integrations)
   ↓
Execution Engine
   ↓
Database (Patterns + History)
```

---

## Status
✅ All endpoints implemented and production-ready
✅ Groq integration verified
✅ Learning system functional
✅ Caching system active
