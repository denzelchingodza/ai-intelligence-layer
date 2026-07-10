import requests
from app.config import SENTINEL_API_URL, SENTINEL_TOKEN


def _auth_headers() -> dict:
    """Cognito JWT auth header, if a token is configured."""
    if SENTINEL_TOKEN:
        return {"Authorization": f"Bearer {SENTINEL_TOKEN}"}
    return {}


def _parse(resp, label: str):
    """Safe JSON parse with a readable error."""
    if not resp.text or not resp.text.strip():
        raise ValueError(
            f"Empty response (HTTP {resp.status_code}) — {label} may be sleeping or unreachable."
        )
    if resp.status_code in (401, 403):
        raise ValueError(
            "Sentinel returned 401/403. Set SENTINEL_TOKEN in your environment to a valid Cognito JWT."
        )
    try:
        return resp.json()
    except Exception:
        snippet = resp.text[:300]
        raise ValueError(f"Non-JSON response (HTTP {resp.status_code}): {snippet}")


def query_sentinel(question: str) -> dict:
    try:
        if not SENTINEL_API_URL:
            return {
                "source": "sentinel",
                "answer": "Sentinel URL is not configured.",
                "metadata": {},
            }

        headers = _auth_headers()
        resp    = requests.get(f"{SENTINEL_API_URL}/monitors", headers=headers, timeout=10)
        monitors = _parse(resp, "Sentinel")

        up   = sum(1 for m in monitors if m.get("status") == "up")
        down = [m for m in monitors if m.get("status") != "up"]

        if down:
            down_names = ", ".join(m.get("name", "unknown") for m in down)
            answer = f"{up} service(s) up. {len(down)} down: {down_names}."
        else:
            answer = f"All {up} service(s) are up."

        return {
            "source": "sentinel",
            "answer": answer,
            "metadata": {"total": len(monitors), "up": up, "down": len(down)},
        }

    except Exception as e:
        return {
            "source": "sentinel",
            "answer": f"Could not reach Sentinel: {str(e)}",
            "metadata": {},
        }
