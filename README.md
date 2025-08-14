I'll quickly scan the config to list required environment variables (.env keys), then provide a concise README with Poetry setup and usage.
Read file: event_finder/config/settings.py

Read file: event_finder/main.py
Read file: event_finder/services/workflow.py
### Project: Upcoming Events Finder

A FastAPI service that searches the web for a given speaker/name, scrapes relevant pages with Firecrawl, extracts structured event data with an LLM, normalizes and filters it, then returns upcoming events.

### Prerequisites
- Python 3.11
- Poetry

### Setup

- Install Poetry (see `https://python-poetry.org/docs/#installation`)
- Install dependencies:
  - `poetry lock`
  - `poetry install`
- Create a `.env` file in the project root with keys below.

### .env keys

- Required:
  - `FIRECRAWL_API_KEY`: Firecrawl API key
  - `OPENAI_API_KEY`: OpenAI API key (used by the local LLM client)
  - `SERPER_API_KEY`: Serper API key (web search)
- Optional (defaults in `event_finder/config/settings.py`):
  - `TOP_N` (default: 20)
  - `FIRECRAWL_TIMEOUT` (seconds, default: 30)
  - `MAX_CONCURRENCY` (default: 8)

Example `.env`:
```
FIRECRAWL_API_KEY=your_firecrawl_key
OPENAI_API_KEY=your_openai_key
SERPER_API_KEY=your_serper_key
TOP_N=20
FIRECRAWL_TIMEOUT=30
MAX_CONCURRENCY=8
```

### Run the API

- Start the server:
  - `poetry run uvicorn event_finder.main:app --reload`
- Visit the interactive docs:
  - Swagger UI: `http://127.0.0.1:8000/docs`

### Usage

- GET `/events`
  - Query params:
    - `name` (required): speaker/person name
    - `event_type` (optional): `in_person` or `online`
  - Example:
    - `http://127.0.0.1:8000/events?name=Rory%20Sutherland`
    - `http://127.0.0.1:8000/events?name=Rory%20Sutherland&event_type=online`

### Notes

- Firecrawl extraction uses a JSON schema and prompt to pull fields:
  - `event_name`, `date` (ISO 8601), `location { name, address, city, country }`, `url`, `speakers[]`, `event_type`.
- The `Event.date` field accepts ISO 8601 timestamps and is normalized in the workflow.
- Results are deduplicated and filtered to only include today and future dates.