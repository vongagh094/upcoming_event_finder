from starlette.config import Config
from starlette.datastructures import Secret

try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

# API Keys
FIRECRAWL_API_KEY = config("FIRECRAWL_API_KEY", cast=Secret, default="")
OPENAI_API_KEY = config("OPENAI_API_KEY", cast=Secret, default="")
SERPER_API_KEY = config("SERPER_API_KEY", cast=Secret, default="")

# Search and extraction settings
TOP_N = config("TOP_N", cast=int, default=20)
FIRECRAWL_TIMEOUT = config("FIRECRAWL_TIMEOUT", cast=int, default=30)
MAX_CONCURRENCY = config("MAX_CONCURRENCY", cast=int, default=8)

