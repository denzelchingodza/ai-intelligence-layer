# AI Intelligence Layer

A personal AI query interface that sits on top of my projects. Instead of navigating dashboards or calling APIs manually, I can ask a plain English question and get a direct answer.

## The idea

I built multiple tools a monitoring service (Sentinel) and a job market tracker (StackScope) and wanted a single place to query all of them without thinking about which API to hit or what format the response is in. This is that layer.

## How it works

A question comes in. GPT4o-mini classifies the intent and routes it to the right connector. The connector calls the relevant internal API, and the model summarises the result into a plain text answer.

```
"Are any of my services down?"
        ↓
   GPT-4o-mini
        ↓
   Sentinel connector → uptime data
        ↓
   "All services are up. Last incident was 4 days ago."
```

## Built with

FastAPI · OpenAI GPT4o-mini · Python · Render · Vercel

---

Built by [Denzel Chingodza](https://denz-platform.vercel.app)
