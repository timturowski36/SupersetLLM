import os

# ─────────────────────────────────────
# Datenbank – Superset Metadaten
# ─────────────────────────────────────
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SQLALCHEMY_DATABASE_URI",
    "postgresql://superset:superset@postgres:5432/superset"
)

# ─────────────────────────────────────
# Security
# ─────────────────────────────────────
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "change-me")
WTF_CSRF_ENABLED = False  # nur für lokale Entwicklung

# ─────────────────────────────────────
# Feature Flags
# ─────────────────────────────────────
FEATURE_FLAGS = {
    "AI_ENABLED": True,
}

# ─────────────────────────────────────
# LLM / AI – Ollama-Konfiguration
# ─────────────────────────────────────
# Ollama gibt eine OpenAI-kompatible API aus.
# Superset denkt, es spricht mit OpenAI –
# spricht aber mit dem lokalen Mistral.
SQLLAB_AI_ENABLED   = True
OPENAI_API_KEY      = os.environ.get("OPENAI_API_KEY",      "ollama")
OPENAI_API_BASE_URL = os.environ.get("OPENAI_API_BASE_URL", "http://ollama:11434/v1")
OPENAI_MODEL_ID     = "mistral:7b-instruct-q4_k_m"
