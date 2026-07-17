# AI Intelligence Layer

A natural language interface across my personal projects. Ask a plain English question, get a plain text answer.

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=flat&logo=render&logoColor=white)

---

## What it does

The AI Intelligence Layer connects StackScope and DocuZen through a single query interface. Instead of navigating dashboards or calling APIs manually, you ask a question and get an answer!

How it works:

1. A question comes in through the API
2. GPT-4o-mini classifies the intent and decides which service to call
3. The relevant connector calls the internal API and returns its data
4. The result is returned as a readable plain text answer

```
"What skills are in demand right now?"
        |
        v
  GPT-4o-mini (intent classification)
        |
        v
  StackScope connector  -->  live job market data
        |
        v
  "Python, SQL and React are the most in-demand skills this week."
```

The connector architecture means adding a new service is one new file. Rate limiting is in place to control API costs.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python |
| AI | OpenAI GPT-4o-mini |
| Deployment | Render (API), Vercel (frontend) |

---

## Running locally

**1. Clone and install**

```bash
git clone https://github.com/denz-os/ai-intelligence-layer.git
cd ai-intelligence-layer
pip install -r requirements.txt
```

**2. Create a `.env` file**

```env
OPENAI_API_KEY=your_openai_key
STACKSCOPE_API_URL=your_stackscope_api_url
DOCUZEN_API_URL=your_docuzen_api_url
```

**3. Run**

```bash
uvicorn app.main:app --reload
```

---

## What I learned

I had already built several tools that worked independently. This project was about making them talk to each other through a layer that any person could use without knowing what was underneath.

That is a different kind of engineering problem. Designing the connector architecture, thinking about how intent classification should work, and handling cases where the model is uncertain about which service to call pushed me to think about software composition in a way none of my earlier projects had. It is the project that most directly reflects where my interest in AI engineering is going.

---

## Part of

This service is one component of a larger personal infrastructure.
