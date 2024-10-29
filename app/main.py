from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import requests
from serpapi import GoogleSearch
from services import GenerateLeadsService

app = FastAPI(title="Lead Generation API", description="API to generate leads by location and industry", version="1.0.0")

class LocationData(BaseModel):
    location: str
    industry: str
    min_results: int = 50

@app.post("/generate-leads/", response_class=FileResponse)
async def generate_leads(location_data: LocationData):
    try:
        service = GenerateLeadsService(location_data.location, location_data.industry, location_data.min_results)
        file_path = await service.run()
        if not file_path:
            raise HTTPException(status_code=404, detail="Leads not found for the given parameters.")
        return FileResponse(path=file_path, filename=file_path, media_type='application/octet-stream')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)
    
@app.get("/proxy-locations/")
async def proxy_locations(q: str):
    try:
        response = requests.get(f"https://serpapi.com/locations.json?q={q}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))