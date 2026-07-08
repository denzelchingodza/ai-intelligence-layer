from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.router import route
from app.config import ALLOWED_ORIGINS

app = FastAPI(title="AI Intelligence Layer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGINS],
    allow_methods=["*"],
    allow_headers=["*"],

)
class QueryRequest(BaseModel):
    query; str
@app.get("/health")
def health():
    return{"status": "ok"}
@app.post("/query")
def handle_query(body: QueryRequest):
    return route(body.query)
