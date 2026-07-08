import requests
from app.config import SENTINEL_API_URL


def query_sentinel(question: str) -> dict:
    try:
        if not SENTINEL_API_URL:
            return {
                "source": "sentinel",
                "answer": "Sentinel URL is not configured.",
                "metadata": {}
            }

        resp = requests.get(f"{SENTINEL_API_URL}/monitors", timeout=10)
        resp.raise_for_status()
        monitors = resp.json()

        up = sum(1 for m in monitors if m.get("status") == "up")
        down = [m for m in monitors if m.get("status") != "up"]

        if down:
            down_names = ", ".join(m.get("name", "unknown") for m in down)
            answer = f"{up} service(s) up. {len(down)} down: {down_names}."
        else:
            answer = f"All {up} service(s) are up."

        return {
            "source": "sentinel",
            "answer": answer,
            "metadata": {"total": len(monitors), "up": up, "down": len(down)}
        }

    except Exception as e:
        return {
            "source": "sentinel",
            "answer": f"Could not reach Sentinel: {str(e)}",
            "metadata": {}
        }


