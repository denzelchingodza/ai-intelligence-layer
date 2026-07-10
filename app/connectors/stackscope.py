import json
import requests
from openai import OpenAI
from app.config import STACKSCOPE_API_URL, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def _parse(resp) -> dict:
    """
    Safe JSON parse. Raises a clear error instead of a cryptic JSONDecodeError
    when the service is sleeping or returns an unexpected response.
    """
    if not resp.text or not resp.text.strip():
        raise ValueError(
            f"Empty response (HTTP {resp.status_code}) — StackScope may be sleeping. "
            "Wait ~30 seconds for Render to wake it up and try again."
        )
    try:
        return resp.json()
    except Exception:
        snippet = resp.text[:300]
        raise ValueError(f"Non-JSON response (HTTP {resp.status_code}): {snippet}")


def extract_params(question: str) -> dict:
    """
    Uses GPT to pull structured data out of a natural language question.
    Returns skills list and experience level so we can call StackScope endpoints.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract skills and experience level from the user's question. "
                    "Return JSON with two keys: "
                    "'skills' (list of skill names, empty list if none mentioned) and "
                    "'experience_level' (one of: junior, mid, senior — or null if not mentioned)."
                ),
            },
            {"role": "user", "content": question},
        ],
    )
    return json.loads(response.choices[0].message.content)


def query_stackscope(question: str) -> dict:
    """
    Routes to the right StackScope endpoint based on intent keywords in the question,
    then calls the API with extracted parameters.
    """
    if not STACKSCOPE_API_URL:
        return {"source": "stackscope", "answer": "StackScope is not configured.", "metadata": {}}

    q = question.lower()

    try:
        # Salary prediction
        if any(word in q for word in ["salary", "earn", "pay", "paid", "money", "rate"]):
            params = extract_params(question)
            skills = params.get("skills", [])
            level  = params.get("experience_level") or "mid"
            if not skills:
                return {
                    "source": "stackscope",
                    "answer": "Please mention specific skills for a salary prediction.",
                    "metadata": {},
                }
            resp = requests.post(
                f"{STACKSCOPE_API_URL}/api/salary/predict",
                json={"skills": skills, "experience_level": level},
                timeout=15,
            )
            result = _parse(resp)
            answer = f"Predicted salary for {', '.join(skills)} at {level} level: {result.get('predicted_salary_range', result)}"

        # Gap analysis
        elif any(word in q for word in ["gap", "missing", "learn next", "improve", "lacking"]):
            params = extract_params(question)
            skills = params.get("skills", [])
            resp   = requests.post(f"{STACKSCOPE_API_URL}/api/gap", json={"skills": skills}, timeout=15)
            result = _parse(resp)
            answer = f"Gap analysis: {result}"

        # Job matching
        elif any(word in q for word in ["match", "jobs for me", "roles", "positions", "fit"]):
            params = extract_params(question)
            skills = params.get("skills", [])
            resp   = requests.post(f"{STACKSCOPE_API_URL}/api/match", json={"skills": skills}, timeout=15)
            result = _parse(resp)
            answer = f"Top matching jobs: {result}"

        # Emerging / trending up
        elif any(word in q for word in ["emerging", "growing", "rising", "up and coming"]):
            resp   = requests.get(f"{STACKSCOPE_API_URL}/api/trends/emerging", timeout=15)
            result = _parse(resp)
            answer = f"Emerging skills: {result}"

        # Declining
        elif any(word in q for word in ["declining", "falling", "dying", "losing demand"]):
            resp   = requests.get(f"{STACKSCOPE_API_URL}/api/trends/declining", timeout=15)
            result = _parse(resp)
            answer = f"Declining skills: {result}"

        # General trends (default)
        else:
            resp   = requests.get(f"{STACKSCOPE_API_URL}/api/trends", timeout=15)
            result = _parse(resp)
            answer = f"Current skill trends: {result}"

    except Exception as e:
        return {"source": "stackscope", "answer": f"Could not reach StackScope: {e}", "metadata": {}}

    return {"source": "stackscope", "answer": answer, "metadata": {}}
