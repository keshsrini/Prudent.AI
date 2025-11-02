# Price Gap API

A minimal FastAPI application with two endpoints for price gap analysis and movie search.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your TMDB API key:

```
TMDB_API_KEY=your_api_key_here
```

3. Run the application:

```bash
python -m uvicorn app:app --reload
```

## Endpoints

- `POST /api/price-gap-pair` - Find price gap pairs
- `GET /api/movies` - Search movies with director info
