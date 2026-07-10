import os

# Backend URLs
SENTINEL_API_URL   = os.getenv("SENTINEL_API_URL", "")
SENTINEL_TOKEN     = os.getenv("SENTINEL_TOKEN", "")   # Cognito JWT for Sentinel auth
STACKSCOPE_API_URL = os.getenv("STACKSCOPE_API_URL", "")
DOCUZEN_API_URL    = os.getenv("DOCUZEN_API_URL", "")

OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
