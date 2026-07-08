from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.router import route
from app.config import ALLOWED_ORIGINS

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGINS],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class QueryRequest(BaseModel):
    query: str

    @field_validator("query")
    @classmethod
    def query_length(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty.")
        if len(v) > 500:
            raise ValueError("Query must be under 500 characters.")
        return v


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/query")
@limiter.limit("10/hour")
async def handle_query(request: Request, body: QueryRequest):
    try:
        return route(body.query)
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={"source": "error", "answer": f"Something went wrong: {str(e)}", "metadata": {}}
        )