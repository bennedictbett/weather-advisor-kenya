"""
Shamba Weather Advisor — WeatherAI API Integration
A hyperlocal weather advisory tool for Kenyan farmers, combining
WeatherAI's forecast + tree analysis APIs with an LLM-generated
farming-specific recommendation layer.
"""

import os
import httpx
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

WEATHER_AI_KEY = os.getenv("WEATHER_AI_KEY")
WEATHER_AI_BASE = "https://api.weather-ai.co"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE = "https://api.groq.com/openai/v1"

app = FastAPI(
    title="Shamba Weather Advisor",
    description="Hyperlocal weather + agronomic insights for Kenyan farmers, powered by WeatherAI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class WeatherRequest(BaseModel):
    lat: float
    lon: float
    days: Optional[int] = 7
    crop: Optional[str] = None  # e.g. "maize", "tea" — used for farming context


def get_headers():
    if not WEATHER_AI_KEY:
        raise HTTPException(status_code=500, detail="WEATHER_AI_KEY not configured on server")
    return {"Authorization": f"Bearer {WEATHER_AI_KEY}"}


@app.get("/")
def root():
    return {
        "service": "Shamba Weather Advisor",
        "status": "running",
        "endpoints": ["/weather", "/trees/analyze", "/health"]
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/weather")
async def get_weather(lat: float, lon: float, days: int = 7, crop: Optional[str] = None):
    """
    Fetch weather forecast for a location and generate a farming-specific
    recommendation based on crop type (if provided).
    """
    params = {"lat": lat, "lon": lon, "days": days, "ai": "true", "units": "metric", "lang": "en"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                f"{WEATHER_AI_BASE}/v1/weather",
                headers=get_headers(),
                params=params
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"WeatherAI error: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Could not reach WeatherAI: {str(e)}")

        weather_data = resp.json()

    # Build a simple rule-based advisory layer on top of WeatherAI's own summary
    advisory = build_farming_advisory(weather_data, crop)

    # Enrich with an LLM-generated, source-grounded narrative advisory
    llm_advisory = await generate_llm_advisory(weather_data, advisory, crop)
    advisory["ai_narrative"] = llm_advisory

    return {
        "location": {"lat": lat, "lon": lon},
        "weather": weather_data,
        "farming_advisory": advisory
    }


async def generate_llm_advisory(weather_data: dict, rule_based_advisory: dict, crop: Optional[str]) -> str:
    """
    Uses an LLM (via Groq) to generate a natural-language farming advisory,
    grounded strictly in the WeatherAI forecast data and the rule-based risk
    flags already computed. This mirrors the grounded-generation pattern used
    in the author's M-Pesa RAG project: the model is given only verified
    source data and instructed not to invent information beyond it.
    """
    if not GROQ_API_KEY:
        return "AI narrative unavailable — GROQ_API_KEY not configured."

    crop_label = crop or "general farming"

    system_prompt = (
        "You are an agronomic weather advisor for Kenyan smallholder farmers. "
        "You must base your response ONLY on the forecast data and risk flags provided. "
        "Do not invent weather conditions not present in the data. "
        "Write 2-3 short, practical sentences in plain English, addressed directly to the farmer. "
        "Be specific and actionable, not generic."
    )

    user_prompt = (
        f"Crop: {crop_label}\n"
        f"Risk flags detected: {rule_based_advisory.get('risk_flags', [])}\n"
        f"Rule-based recommendations already generated: {rule_based_advisory.get('recommendations', [])}\n"
        f"Raw forecast summary (truncated): {json.dumps(weather_data)[:1500]}\n\n"
        "Write a short, farmer-facing advisory paragraph based strictly on the above."
    )

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 220
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"AI narrative generation failed: {str(e)}"


def build_farming_advisory(weather_data: dict, crop: Optional[str]) -> dict:
    """
    Lightweight rule-based advisory layer that translates raw forecast data
    into actionable guidance for Kenyan smallholder farmers.
    This sits on top of WeatherAI's own Gemini summary, adding crop-specific framing.
    """
    risk_flags = []
    recommendations = []

    # Defensive parsing — actual response shape may vary, this handles common patterns
    daily = weather_data.get("daily") or weather_data.get("forecast") or []

    rain_days = 0
    high_wind_days = 0

    for day in daily if isinstance(daily, list) else []:
        precip = day.get("precip_mm") or day.get("precipitation") or 0
        wind = day.get("wind_kph") or day.get("wind_speed") or 0
        if precip and precip > 10:
            rain_days += 1
        if wind and wind > 40:
            high_wind_days += 1

    if rain_days >= 3:
        risk_flags.append("heavy_rain")
        recommendations.append("Heavy rain expected on multiple days — delay planting or harvesting where possible, and check drainage.")

    if high_wind_days >= 1:
        risk_flags.append("high_wind")
        recommendations.append("High winds forecasted — secure young plants and check for structural damage risk on tall crops.")

    if crop:
        crop_lower = crop.lower()
        if crop_lower in ["maize", "corn"] and rain_days >= 2:
            recommendations.append("For maize: moderate rain is favorable for germination, but monitor for waterlogging in low-lying plots.")
        elif crop_lower == "tea" and high_wind_days >= 1:
            recommendations.append("For tea: wind can damage young shoots — consider windbreak checks this week.")

    if not recommendations:
        recommendations.append("No significant weather risks detected for the forecast period. Normal farming activities can proceed.")

    return {
        "crop_context": crop or "general",
        "risk_flags": risk_flags,
        "recommendations": recommendations
    }


@app.post("/trees/analyze")
async def analyze_trees(
    image: UploadFile = File(...),
    county: Optional[str] = Form(None),
    landAcres: Optional[float] = Form(None),
    notes: Optional[str] = Form(None)
):
    """
    Proxy to WeatherAI's tree/canopy analysis endpoint — count tree crowns,
    assess canopy health, and surface agronomic recommendations from a farm photo.
    """
    image_bytes = await image.read()

    files = {"image": (image.filename, image_bytes, image.content_type)}
    data = {}
    if county:
        data["county"] = county
    if landAcres:
        data["landAcres"] = str(landAcres)
    if notes:
        data["notes"] = notes

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{WEATHER_AI_BASE}/v1/trees/analyze",
                headers=get_headers(),
                files=files,
                data=data
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"WeatherAI error: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Could not reach WeatherAI: {str(e)}")

        return resp.json()


@app.get("/usage")
async def get_usage():
    """Check current API usage against WeatherAI plan limits."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{WEATHER_AI_BASE}/v1/usage", headers=get_headers())
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        return resp.json()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)