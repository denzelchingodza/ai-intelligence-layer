import requests
from app.config import SENTINEL_API_URL
def query_sentinel(question: str) -> dict:
    """
    Fetches monitor and incident data from Sentinel and returns a summary.
    The question isn't used for search here. Sentinel is status only,
    so we just return the current state of all monitors.
    """
    if not SENTINEL_API_URL:
        return {"source": "sentinel", "answer": "Sentinel is not configured.", "metadata": {}}
    try: 
        monitors = requests.get(f"{SENTINEL_API_URL}/monitors", timeout=10).json()
    except Exception as e:
        return{"source": "sentinel", "answer": f"Couldn't reach Sentinel: {e}", "metadata": {}}
    if not monitors:
        return{"source": "sentinel", "answer": "No monitors found.", "metadata": {}}
    
    up = [m for m in monitors if m.get("lastStatus") == "up" ]
    down = [m for m in monitors if m.get("lastStatus") == "down"]
    unknown = [m for m in monitors if m.get("lastStatus") not in ("up", "down")]

    lines = []
    if up:
        lines.append(f"{len(up)} monitor(s) UP: {','.join(m['name'] for m in up)}")
    if down:
        lines.append(f"{len(down)} monitor(s) DOWN: {', '.join(m['name'] for m in down)}")
    if unknown:
        lines.append(f"{len(unknown)} monitor(s) with unknown status.")
    
    answer = " | ".join(lines) if lines else "All monitors reporting unknown status."
    return {
        "source": "sentinel",
        "answer": answer,
        "metadata": {"total": len(monitors), "up": len(up), "down": len(down)},


    }


