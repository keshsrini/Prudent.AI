import os
import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv
from price_gap import find_price_gap_pair

load_dotenv()

app = FastAPI()

class PriceGapRequest(BaseModel):
    nums: list[int]
    k: int = Field(ge=0)

@app.post("/api/price-gap-pair")
async def price_gap_pair(request: PriceGapRequest):
    result = find_price_gap_pair(request.nums, request.k)
    
    if result is None:
        return {"indices": None, "values": None}
    
    i, j = result
    return {
        "indices": [i, j],
        "values": [request.nums[i], request.nums[j]]
    }

@app.get("/api/movies")
async def movies(q: Optional[str] = Query(None), page: int = Query(1, ge=1)):
    if not q:
        return {"movies": [], "page": page, "total_pages": 0, "total_results": 0}
    
    api_key = os.getenv("TMDB_API_KEY")
    
    url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": api_key, "query": q, "page": page}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(2):
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                movies = []
                for movie in data.get("results", []):
                    # Get director from credits
                    credits_url = f"https://api.themoviedb.org/3/movie/{movie['id']}/credits"
                    try:
                        credits_response = await client.get(credits_url, params={"api_key": api_key})
                        credits_response.raise_for_status()
                        credits_data = credits_response.json()
                        
                        director = "Unknown"
                        for crew in credits_data.get("crew", []):
                            if crew.get("job") == "Director":
                                director = crew.get("name", "Unknown")
                                break
                    except:
                        director = "Unknown"
                    
                    movies.append({
                        "title": movie.get("title", "Unknown"),
                        "director": director
                    })
                
                return {
                    "movies": movies,
                    "page": data.get("page", page),
                    "total_pages": data.get("total_pages", 0),
                    "total_results": data.get("total_results", 0)
                }
                
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt == 0:
                    continue
                raise HTTPException(status_code=502, detail="External API unavailable")