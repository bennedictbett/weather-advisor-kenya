"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const QUICK_LOCATIONS = [
  { name: "Eldoret", lat: -0.5143, lon: 35.2698 },
  { name: "Nairobi", lat: -1.2921, lon: 36.8219 },
  { name: "Bomet", lat: -0.6743, lon: 35.3416 },
  { name: "Nakuru", lat: -0.3031, lon: 36.0800 },
];

const CROPS = [
  { value: "", label: "General" },
  { value: "maize", label: "Maize" },
  { value: "tea", label: "Tea" },
  { value: "beans", label: "Beans" },
  { value: "coffee", label: "Coffee" },
];

interface WeatherResult {
  location: { lat: number; lon: number };
  weather: Record<string, unknown>;
  farming_advisory: {
    crop_context: string;
    risk_flags: string[];
    recommendations: string[];
    ai_narrative?: string;
  };
}

export default function Home() {
  const [lat, setLat] = useState(-0.5143);
  const [lon, setLon] = useState(35.2698);
  const [days, setDays] = useState(7);
  const [crop, setCrop] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WeatherResult | null>(null);

  async function fetchWeather() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const params = new URLSearchParams({
        lat: String(lat),
        lon: String(lon),
        days: String(days),
      });
      if (crop) params.append("crop", crop);

      const res = await fetch(`${API_BASE}/weather?${params}`);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Request failed");
      }

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-[#1a472a] to-[#2d6a4f] px-4 py-10">
      <div className="mx-auto max-w-2xl">
        <header className="mb-8 text-center text-white">
          <h1 className="text-3xl font-bold tracking-tight">
            🌦️ Shamba Weather Advisor
          </h1>
          <p className="mt-2 text-sm text-white/80">
            Hyperlocal weather + farming insights for Kenya, powered by{" "}
            <span className="font-semibold">WeatherAI</span>
          </p>
        </header>

        <div className="rounded-2xl bg-white p-6 shadow-xl">
          {/* Quick locations */}
          <div className="mb-4 flex flex-wrap gap-2">
            {QUICK_LOCATIONS.map((loc) => (
              <button
                key={loc.name}
                onClick={() => {
                  setLat(loc.lat);
                  setLon(loc.lon);
                }}
                className="rounded-full border border-[#2d6a4f] bg-[#e8f5e9] px-3 py-1 text-sm font-medium text-[#2d6a4f] transition hover:bg-[#2d6a4f] hover:text-white"
              >
                {loc.name}
              </button>
            ))}
          </div>

          {/* Lat / Lon */}
          <div className="mb-4 grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-gray-600">
                Latitude
              </label>
              <input
                type="number"
                step="0.0001"
                value={lat}
                onChange={(e) => setLat(parseFloat(e.target.value))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#2d6a4f] focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-gray-600">
                Longitude
              </label>
              <input
                type="number"
                step="0.0001"
                value={lon}
                onChange={(e) => setLon(parseFloat(e.target.value))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#2d6a4f] focus:outline-none"
              />
            </div>
          </div>

          {/* Days / Crop */}
          <div className="mb-5 grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-gray-600">
                Forecast Days
              </label>
              <select
                value={days}
                onChange={(e) => setDays(parseInt(e.target.value))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#2d6a4f] focus:outline-none"
              >
                <option value={3}>3 days</option>
                <option value={7}>7 days</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-gray-600">
                Crop (optional)
              </label>
              <select
                value={crop}
                onChange={(e) => setCrop(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#2d6a4f] focus:outline-none"
              >
                {CROPS.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={fetchWeather}
            disabled={loading}
            className="w-full rounded-xl bg-[#2d6a4f] py-3 font-semibold text-white transition hover:bg-[#1a472a] disabled:bg-gray-400"
          >
            {loading ? "Loading..." : "Get Weather Advisory"}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-700 shadow">
            Error: {error}
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="mt-4 space-y-4">
            <div className="rounded-2xl bg-white p-6 shadow-xl">
              <h2 className="mb-3 text-xs font-bold uppercase tracking-wide text-[#2d6a4f]">
                Farming Advisory
                {result.farming_advisory.crop_context &&
                  ` — ${result.farming_advisory.crop_context}`}
              </h2>

              {result.farming_advisory.ai_narrative && (
                <div className="mb-4 rounded-xl bg-gradient-to-r from-[#1a472a] to-[#2d6a4f] p-4 text-sm text-white">
                  <div className="mb-1 flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-white/80">
                    <span>🤖</span> AI Advisory
                  </div>
                  {result.farming_advisory.ai_narrative}
                </div>
              )}

              {result.farming_advisory.risk_flags.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-2">
                  {result.farming_advisory.risk_flags.map((flag) => (
                    <span
                      key={flag}
                      className="rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-800"
                    >
                      ⚠️ {flag.replace("_", " ")}
                    </span>
                  ))}
                </div>
              )}

              <div className="space-y-2">
                {result.farming_advisory.recommendations.map((rec, i) => (
                  <div
                    key={i}
                    className="rounded-r-lg border-l-4 border-[#2d6a4f] bg-[#f1f8f4] px-4 py-2 text-sm text-gray-800"
                  >
                    {rec}
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl bg-white p-6 shadow-xl">
              <h2 className="mb-3 text-xs font-bold uppercase tracking-wide text-[#2d6a4f]">
                Raw Weather Data
              </h2>
              <pre className="max-h-72 overflow-auto rounded-lg bg-gray-50 p-3 text-xs">
                {JSON.stringify(result.weather, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}