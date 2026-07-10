import requests
from app.config import DOCUZEN_API_URL


def _parse(resp, label: str):
    """Safe JSON parse with a readable error."""
    if not resp.text or not resp.text.strip():
        raise ValueError(
            f"Empty response (HTTP {resp.status_code}) — {label} may be sleeping. "
            "Wait ~30 seconds for Render to wake it up and try again."
        )
    try:
        return resp.json()
    except Exception:
        snippet = resp.text[:300]
        raise ValueError(f"Non-JSON response (HTTP {resp.status_code}): {snippet}")


def query_docuzen(question: str) -> dict:
    """
    Fetches the most recently uploaded document from DocuZen
    and asks it the question. Returns the answer with page citations.
    """
    if not DOCUZEN_API_URL:
        return {"source": "docuzen", "answer": "DocuZen is not configured.", "metadata": {}}

    try:
        resp = requests.get(f"{DOCUZEN_API_URL}/documents/", timeout=15)
        docs = _parse(resp, "DocuZen")
    except Exception as e:
        return {"source": "docuzen", "answer": f"Could not reach DocuZen: {e}", "metadata": {}}

    if not docs:
        return {
            "source": "docuzen",
            "answer": "No document is currently uploaded in DocuZen. Upload one first then ask your question.",
            "metadata": {},
        }

    doc    = docs[0]
    doc_id = doc["id"]

    if doc.get("status") != "ready":
        return {
            "source": "docuzen",
            "answer": f"The current document ({doc['filename']}) is still processing. Try again in a moment.",
            "metadata": {"document_id": doc_id, "status": doc.get("status")},
        }

    try:
        resp   = requests.post(
            f"{DOCUZEN_API_URL}/chat/",
            json={"document_id": doc_id, "question": question},
            timeout=30,
        )
        result = _parse(resp, "DocuZen chat")
    except Exception as e:
        return {"source": "docuzen", "answer": f"DocuZen chat failed: {e}", "metadata": {}}

    return {
        "source": "docuzen",
        "answer": result.get("answer", "No answer returned."),
        "metadata": {
            "document": doc["filename"],
            "sources": result.get("sources", []),
        },
    }
