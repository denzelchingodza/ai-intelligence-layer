"""
Muzezuru connector — Shona-language conversational AI.

Model:  denzelchingodza/muzezuru
Base:   bigscience/bloomz-3b (QLoRA, rank-16 LoRA adapters)
Hosted: Hugging Face Inference API + ZeroGPU Space

Known weaknesses (manual eval, 15-prompt scorecard):
  - Factual / geographic accuracy
  - Instruction-following
  - Greetings / small talk
A caveat is automatically appended when a query or response touches these areas.
"""

import time
import requests
from app.config import HF_API_TOKEN

_INFERENCE_URL = "https://api-inference.huggingface.co/models/denzelchingodza/muzezuru"

# Keywords that signal the response may be factually weak
_FACTUAL_KW = [
    # English terms likely to elicit geographic/historical claims
    "capital", "population", "president", "who is", "where is", "when was",
    "history", "founded", "language of", "country",
    # Shona equivalents
    "guta", "nyika", "ndiani", "kupi", "mambo", "musoro wehurumende",
    "makore mangani", "nguvai",
]
_GREETING_KW = [
    "mhoro", "maswera", "mangwanani", "masikati", "manheru", "makadii",
    "hello", "hi ", "good morning", "how are you",
]
_CAVEAT = (
    "\n\n⚠️  Muzezuru note: this model is weaker on factual, geographic, and greeting "
    "queries — responses in these areas may be inaccurate. Please verify important "
    "facts independently."
)


def _needs_caveat(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _FACTUAL_KW + _GREETING_KW)


def _format_prompt(message: str) -> str:
    """
    Alpaca-style instruction template used during fine-tuning on
    saillab/alpaca_shona_taco (after data-contamination fix).
    """
    return (
        "Below is an instruction in Shona. Write a helpful response in Shona.\n\n"
        f"### Instruction:\n{message}\n\n"
        "### Response:\n"
    )


def query_muzezuru(question: str) -> dict:
    if not HF_API_TOKEN:
        return {
            "source": "muzezuru",
            "answer": (
                "Muzezuru is not configured — HF_API_TOKEN environment variable is missing. "
                "Add it in Render's environment settings."
            ),
            "metadata": {},
        }

    prompt  = _format_prompt(question)
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 220,
            "temperature": 0.75,
            "do_sample": True,
            "return_full_text": False,
        },
        # Tell HF to wait for model load instead of returning 503 immediately
        "options": {"wait_for_model": True},
    }

    for attempt in range(3):
        try:
            resp = requests.post(_INFERENCE_URL, headers=headers, json=payload, timeout=90)

            if resp.status_code == 503:
                # Model is still loading even with wait_for_model=True
                if attempt < 2:
                    time.sleep(15)
                    continue
                return {
                    "source": "muzezuru",
                    "answer": (
                        "Muzezuru is still loading on Hugging Face (cold start can take ~30 s). "
                        "Please try again in a moment."
                    ),
                    "metadata": {},
                }

            if resp.status_code != 200:
                return {
                    "source": "muzezuru",
                    "answer": f"Muzezuru returned HTTP {resp.status_code}. Please try again.",
                    "metadata": {"http_status": resp.status_code},
                }

            result = resp.json()

            # HF text-generation API: [{"generated_text": "..."}]
            if isinstance(result, list) and result:
                generated = result[0].get("generated_text", "").strip()
            elif isinstance(result, dict):
                generated = result.get("generated_text", "").strip()
            else:
                generated = str(result).strip()

            if not generated:
                generated = (
                    "Ndisati ndanzwisisa mubvunzo uyu. "
                    "(Muzezuru could not generate a response — try rephrasing your question.)"
                )

            if _needs_caveat(question) or _needs_caveat(generated):
                generated += _CAVEAT

            return {
                "source": "muzezuru",
                "answer": generated,
                "metadata": {
                    "model": "denzelchingodza/muzezuru",
                    "base_model": "bigscience/bloomz-3b",
                    "method": "QLoRA (rank=16, alpha=32)",
                },
            }

        except requests.exceptions.Timeout:
            if attempt < 2:
                time.sleep(10)
                continue
            return {
                "source": "muzezuru",
                "answer": (
                    "Muzezuru timed out — the model may be under load. "
                    "Try again in a moment."
                ),
                "metadata": {},
            }
        except Exception as e:
            return {
                "source": "muzezuru",
                "answer": f"Could not reach Muzezuru: {e}",
                "metadata": {},
            }

    return {
        "source": "muzezuru",
        "answer": "Muzezuru is unavailable right now. Please try again.",
        "metadata": {},
    }
