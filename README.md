# AI Intelligence Layer

A natural language query interface over multiple project APIs. Ask a question in plain English the AI determines which service to query and returns a plain-text answer.

## What it does

Routes natural language questions to the right backend connector using GPT4o-mini. Currently supports:

- **Sentinel** — service uptime, alerts, and health checks
- **StackScope** — developer job trends, skill demand, and salary data

## API

**POST** `/query`

```json
{ "question": "What skills are trending up this month?" }
```

```json
{
  "source": "stackscope",
  "answer": "TypeScript and Kubernetes are trending up.",
  "metadata": {}
}
```

Rate limited to 10 requests/hour.

## Stack

FastAPI · OpenAI GPT4o-mini · Render (API) · Vercel (frontend)

## Setup

```bash
pip install -r requirements.txt
OPENAI_API_KEY=sk-... uvicorn app.main:app --reload
```

**Required env vars:** `OPENAI_API_KEY`, `SENTINEL_API_URL`, `SENTINEL_COGNITO_TOKEN`

---

Built by [Denzel Chingodza](https://denz-platform.vercel.app)
