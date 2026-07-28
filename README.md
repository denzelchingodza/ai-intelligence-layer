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

## What broke and how I fixed it

**GPT returning inconsistent classification output**

Early versions of the router prompt asked GPT to "identify which tool to use". The model would return things like `"I think this is a stackscope question"` or `"The answer is: docuzen"` instead of the bare word. The downstream `if tool == "stackscope"` check would always fall through to the else branch. Fixed by making the prompt extremely explicit "Reply with only the single word: stackscope or docuzen. Nothing else." combined with `.strip().lower()` on the response and an explicit else branch that returns a readable fallback:

```python
else:
    return {
        "source": "unknown",
        "answer": "Could not determine which tool to use. Try rephrasing your question.",
        "metadata": {"raw_classification": tool},
    }
```

**API errors crashing the frontend**

When a downstream connector threw an exception (StackScope API down, OpenAI timeout), the unhandled error bubbled up as a 500 response. The Next.js frontend had no error handling for 500s and broke silently. Fixed by catching all exceptions in the route handler and returning a structured 200 response with the error message in the body the frontend always gets a renderable object:

```python
except Exception as e:
    return JSONResponse(
        status_code=200,
        content={"source": "error", "answer": f"Something went wrong: {str(e)}", "metadata": {}}
    )
```

**CORS blocking cross-origin requests**

The frontend on Vercel and the API on Render are different origins. Without CORS middleware, the browser blocked all POST requests before they reached the server. Added `CORSMiddleware` with allowed origins read from an environment variable rather than hardcoded, so both local and production origins work.

**OpenAI costs during development**

Every query hits GPT twice once for classification and once inside the connector for the answer. Without a rate limit, rapid testing during development added up quickly. Added `slowapi` with a 10 requests/hour limit per IP to protect costs in production.

---

## Technical notes

- **Classification model** — GPT-4o-mini is used for both the intent classifier and the connector answer generation. It's accurate enough for binary classification at a fraction of the cost of GPT-4.
- **Connector pattern** — each connector (`stackscope.py`, `docuzen.py`) is a standalone module that knows how to call one service and return a normalised `{source, answer, metadata}` dict. The router doesn't know what's inside the connector. Adding a new service means writing one new file and one new `elif` branch in `route()`.
- **Query validation** — Pydantic's `field_validator` strips whitespace and rejects empty queries and anything over 500 characters before the request reaches the router, avoiding unnecessary API calls.
- **Rate limiting** — `slowapi` uses the client IP as the rate limit key (`get_remote_address`). The 10/hour limit is intentionally low because every query triggers at least one OpenAI call.

---

## Part of

This service is one component of a larger personal infrastructure.
