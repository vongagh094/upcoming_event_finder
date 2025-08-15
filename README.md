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
  - `SERPER_API_KEY`: Serper API key (web search)
- Optional (defaults in `event_finder/config/settings.py`):
  - `TOP_N_URLS` (default: 20)
  - `EXTRACT_BATCH_SIZE` (default: 5)

Example `.env`:
```
FIRECRAWL_API_KEY=your_firecrawl_key
SERPER_API_KEY=your_serper_key
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
