import json
import time
import requests
from openai import OpenAI
from app.config import STACKSCOPE_API_URL, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def _wake(url: str, retries: int = 6, interval: int = 10) -> bool:
    """
    Ping the health endpoint until it returns 200 or we run out of retries.
    Gives Render's free tier up to ~60s to wake up before the real query.
    """
    for _ in range(retries):
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


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


def _format_skills_list(label: str, result) -> str:
    """Turn a list of skill dicts or strings into a readable sentence."""
    if not result:
        return f"No {label.lower()} data yet — StackScope may need a scrape run to populate its database."
    # result is usually a list of dicts like {"skill": "python", "count": 42}
    if isinstance(result, list):
        names = []
        for item in result[:10]:
            if isinstance(item, dict):
                skill = item.get("skill") or item.get("name") or str(item)
                count = item.get("count") or item.get("frequency") or item.get("jobs")
                names.append(f"{skill} ({count} jobs)" if count else skill)
            else:
                names.append(str(item))
        return f"{label}: {', '.join(names)}."
    return f"{label}: {result}"


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

    # Wake StackScope up if it's sleeping on Render's free tier
    awake = _wake(f"{STACKSCOPE_API_URL}/api/health")
    if not awake:
        return {
            "source": "stackscope",
            "answer": "StackScope is taking too long to start. It may be overloaded. Try again in a minute.",
            "metadata": {},
        }

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
            low  = result.get("predicted_min") or result.get("min")
            high = result.get("predicted_max") or result.get("max")
            conf = result.get("confidence", "")
            based = result.get("based_on", "")
            if low and high:
                answer = (
                    f"Predicted salary for {', '.join(skills)} at {level} level: "
                    f"${low:,.0f} – ${high:,.0f}"
                    + (f" (confidence: {conf}, based on {based} jobs)" if conf else "")
                )
            else:
                answer = f"Salary data for {', '.join(skills)}: {result}"

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
            answer = _format_skills_list("Emerging skills", result)

        # Declining
        elif any(word in q for word in ["declining", "falling", "dying", "losing demand"]):
            resp   = requests.get(f"{STACKSCOPE_API_URL}/api/trends/declining", timeout=15)
            result = _parse(resp)
            answer = _format_skills_list("Declining skills", result)

        # General trends (default)
        else:
            resp   = requests.get(f"{STACKSCOPE_API_URL}/api/trends", timeout=15)
            result = _parse(resp)
            answer = _format_skills_list("Top skills in demand", result)

    except Exception as e:
        return {"source": "stackscope", "answer": f"Could not reach StackScope: {e}", "metadata": {}}

    return {"source": "stackscope", "answer": answer, "metadata": {}}
