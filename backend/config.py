import os
from pathlib import Path

# Load .env once at import time.
# Looks for backend/.env first, then project-root/.env.
try:
    from dotenv import load_dotenv
    _here = Path(__file__).resolve().parent
    for candidate in (_here / '.env', _here.parent / '.env'):
        if candidate.exists():
            load_dotenv(candidate, override=False)
            break
except ImportError:
    # python-dotenv not installed — fall back to plain os.environ
    pass


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'shophub-dev-secret-key-change-in-prod')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///shophub.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Aliyun DashScope (OpenAI-compatible mode) — used by the AI assistant.
    DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')
    DASHSCOPE_MODEL   = os.environ.get('DASHSCOPE_MODEL',   'qwen-plus')
    DASHSCOPE_URL     = os.environ.get(
        'DASHSCOPE_URL',
        'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    )
