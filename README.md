# 🌦️ Shamba Weather Advisor

A hyperlocal weather and farming advisory tool for Kenyan smallholder farmers, built as a technical integration assessment for **WeatherAI**.

**Live demo:** _[add deployment link here]_
**Backend API docs:** _[add deployment link here]_/docs

---

## What it does

Shamba Weather Advisor consumes the [WeatherAI](https://weather-ai.co) API and layers a Kenya-specific, crop-aware advisory engine on top of the raw forecast data — translating weather signals into actionable guidance for farmers.

A user selects (or enters) a location in Kenya and an optional crop type (maize, tea, beans, coffee). The app:

1. Calls WeatherAI's `/v1/weather` endpoint for a 3–7 day forecast (with WeatherAI's own AI summary enabled via `ai=true`)
2. Runs a custom advisory layer over the forecast — flagging heavy rain and high wind risk, and generating crop-specific recommendations
3. Displays both the human-readable advisory and the raw weather payload

A second endpoint, `/trees/analyze`, proxies WeatherAI's tree/canopy analysis API directly — accepting a farm photo and returning canopy health insights. This wasn't required by the brief but was included to demonstrate integration with more than one WeatherAI capability.

## Why this approach

The brief asked for a clean integration showing how I consume WeatherAI's data and turn it into something functional. Rather than just displaying the raw forecast, I wanted to show product thinking — translating generic weather data into something specific and useful for an actual use case (Kenyan agriculture), which is also the direction I described in my application as the kind of problem I'd want to work on at WeatherAI.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Next.js 14     │  HTTP   │     FastAPI       │  HTTP   │   WeatherAI     │
│   Frontend       │ ──────> │     Backend       │ ──────> │   API           │
│   (TypeScript,   │ <────── │  (Python, httpx)  │ <────── │                 │
│   Tailwind CSS)  │         │                   │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

- **Backend (FastAPI)**: Acts as a thin, typed proxy layer over WeatherAI's API, with the farming advisory logic (`build_farming_advisory`) sitting between the raw API response and what's returned to the frontend.
- **Frontend (Next.js 14 + TypeScript + Tailwind)**: A single-page interface for selecting a location and crop, calling the backend, and rendering the advisory clearly.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, httpx |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| External API | WeatherAI (`/v1/weather`, `/v1/trees/analyze`) |
| Deployment | _[Railway/Render for backend, Vercel for frontend]_ |

## Setup Instructions

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `backend/.env`:
```
WEATHER_AI_KEY=your_weather_ai_key_here
```

Run the server:
```bash
uvicorn main:app --reload
```

API docs available at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Run the dev server:
```bash
npm run dev
```

App available at `http://localhost:3000`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Service info |
| GET | `/health` | Health check |
| GET | `/weather` | Fetch forecast + farming advisory for a location |
| POST | `/trees/analyze` | Proxy to WeatherAI's canopy/tree analysis API |
| GET | `/usage` | Check current WeatherAI API usage against plan limits |

### Example request

```
GET /weather?lat=-0.5143&lon=35.2698&days=7&crop=maize
```

### Example response (shape)

```json
{
  "location": { "lat": -0.5143, "lon": 35.2698 },
  "weather": { ... raw WeatherAI forecast ... },
  "farming_advisory": {
    "crop_context": "maize",
    "risk_flags": ["heavy_rain"],
    "recommendations": [
      "Heavy rain expected on multiple days — delay planting or harvesting where possible, and check drainage.",
      "For maize: moderate rain is favorable for germination, but monitor for waterlogging in low-lying plots."
    ]
  }
}
```

## What I'd build next

Given more time, I'd extend this in a few directions:

- **RAG layer over historical weather + agronomic documentation** — using an LLM (Claude/Groq) to generate richer, source-cited recommendations rather than rule-based ones, similar to a RAG system I've already built for a different domain ([M-Pesa Financial Advisor](https://github.com/bennedictbett/Mpesa-Adviser-Financial-))
- **Caching layer** to reduce redundant WeatherAI API calls for the same location within a short window
- **SMS/WhatsApp delivery** for farmers without reliable smartphone/data access — a more realistic distribution channel for the target users
- **Multi-day risk trend visualization** rather than a flat JSON dump

## Author

**Benedict Bett**
Eldoret, Kenya
[github.com/bennedictbett](https://github.com/bennedictbett)
benedictbett08@gmail.com