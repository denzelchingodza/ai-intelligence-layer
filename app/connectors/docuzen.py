import requests 
from app.config import DOCUZEN_API_URL
def query_docuzen(question: str) -> dict:
    """
    Fetches the most recently uploaded document from DocuZen
    and asks it the question. Returns the answer with page citations.
    
    """
    if not DOCUZEN_API_URL:
        return {"source": "docuzen", "answer": "DocuZen is not configured.", "metadata": {}}
    try: 
        docs = requests.get(f"{DOCUZEN_API_URL}/documents/", timeout=10).json()
    except Exception as e:
        return{"source": "docuzen", "answer": f"Could not reach Docuzen: {e}", "metadata": {}}
    if not docs:
        return {
            "source": "docuzen",
            "answer": "No document is currently uploaded in DocuZen. Upload one first then ask your question.",
            "metadata": {},
        }
    doc = docs[0]
    doc_id = doc["id"]

    if doc.get("status") != "ready":
        return{
             "source": "docuzen",
            "answer": f"The current document ({doc['filename']}) is still processing. Try again in a moment.",
            "metadata": {"document_id": doc_id, "status": doc.get("status")},
        }
    try:
        result = requests.post(
            f"{DOCUZEN_API_URL}/chat/",
            json={"document_id": doc_id, "question": question},
            timeout=30,
        ).json()
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