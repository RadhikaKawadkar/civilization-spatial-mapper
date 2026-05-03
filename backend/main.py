"""
================================================================
  CIVILIZATION SPATIAL INTELLIGENCE MAPPER
  FastAPI Backend — backend/main.py

  Endpoints:
    GET  /                          health check
    GET  /run                       execute C++ engine, stream output
    GET  /api/civilizations         all civilizations
    GET  /api/nearest?lat=&lon=     KD-Tree nearest neighbor
    GET  /api/range                 KD-Tree range query
    GET  /api/cluster?eps=&min=     DBSCAN clustering
    GET  /api/compare?a=&b=         compare two civilizations
    GET  /api/rtree?lat=&lon=       R-Tree region lookup
    GET  /api/stats                 tree statistics

  RUN:
    cd backend
    uvicorn main:app --reload --port 8080
================================================================
"""

import os
import math
import subprocess
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from models import Civilization, ClusterResult
from kdtree import KDTree
from rtree_index import RTreeIndex
from loader import load_civilizations
from clustering import dbscan

load_dotenv()


# ── App setup ──────────────────────────────────────────────────
app = FastAPI(
    title="Civilization Spatial Intelligence Mapper",
    description="KD-Tree + R-Tree spatial queries over historical civilizations",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Bootstrap data & indexes ───────────────────────────────────
DATA_CSV = Path(__file__).parent.parent / "data" / "final_dataset.csv"
CIVS_CSV = Path(__file__).parent.parent / "civilizations.csv"
CPP_EXE  = Path(__file__).parent.parent / "mapper.exe"

all_civs: list[Civilization] = load_civilizations(str(CIVS_CSV) if CIVS_CSV.exists() else str(DATA_CSV))

kd_tree = KDTree()
kd_tree.build(all_civs)

r_tree = RTreeIndex()
r_tree.add_default_regions()

print(f"Loaded {len(all_civs)} civilizations")
print(f"KD-Tree built: {kd_tree.node_count} nodes")
print(f"R-Tree built:  {len(r_tree.regions)} regions")


# ── Routes ─────────────────────────────────────────────────────

@app.get("/")
def health():
    return {
        "status": "running",
        "project": "Civilization Spatial Intelligence Mapper",
        "backend": "FastAPI + Python KD-Tree",
        "endpoints": [
            "/run", "/api/civilizations", "/api/nearest",
            "/api/range", "/api/cluster", "/api/compare",
            "/api/rtree", "/api/stats",
        ],
    }


@app.get("/run", response_class=PlainTextResponse)
def run_cpp_engine():
    """
    Execute the compiled C++ spatial engine and return its stdout.
    Sends a scripted input sequence so the binary runs non-interactively.
    """
    if not CPP_EXE.exists():
        raise HTTPException(
            status_code=404,
            detail=f"C++ executable not found at {CPP_EXE}. Build with: make",
        )
    try:
        # Feed: nearest query (lat=20, lon=78) then exit
        scripted_input = "1\n20\n78\n5\n"
        result = subprocess.run(
            [str(CPP_EXE)],
            input=scripted_input,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout or ""
        if result.returncode != 0 and result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        return output or "[C++ engine produced no output]"
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="C++ engine timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/civilizations")
def get_civilizations():
    return [c.to_dict() for c in all_civs]


@app.get("/api/nearest")
def nearest(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    result = kd_tree.nearest(lat, lon)
    if result is None:
        raise HTTPException(status_code=404, detail="No civilizations loaded")
    civ, dist = result
    return {
        "query": {"lat": lat, "lon": lon},
        "nearest": civ.to_dict(),
        "distance_km": round(dist * 111, 2),
        "algorithm": "KD-Tree O(log n) with branch pruning",
    }


@app.get("/api/range")
def range_query(
    latMin: float = Query(..., ge=-90,  le=90),
    latMax: float = Query(..., ge=-90,  le=90),
    lonMin: float = Query(..., ge=-180, le=180),
    lonMax: float = Query(..., ge=-180, le=180),
):
    if latMin > latMax or lonMin > lonMax:
        raise HTTPException(status_code=400, detail="Min values must be <= Max values")
    results = kd_tree.range_query(latMin, latMax, lonMin, lonMax)
    return {
        "query": {"latMin": latMin, "latMax": latMax, "lonMin": lonMin, "lonMax": lonMax},
        "count": len(results),
        "results": [c.to_dict() for c in results],
        "algorithm": "KD-Tree O(log n + k) spatial pruning",
    }


@app.get("/api/cluster")
def cluster(
    eps: float = Query(default=15.0, gt=0, description="Epsilon radius in degrees (~111 km/degree)"),
    min_pts: int = Query(default=2, ge=1, description="Minimum points to form a cluster"),
):
    """
    DBSCAN clustering using the KD-Tree range search as the epsilon-neighborhood query.
    Returns cluster assignments for every civilization.
    """
    clusters: list[ClusterResult] = dbscan(all_civs, kd_tree, eps, min_pts)
    grouped: dict[int, list] = {}
    for cr in clusters:
        grouped.setdefault(cr.cluster_id, []).append(cr.to_dict())

    return {
        "params": {"eps_degrees": eps, "eps_km": round(eps * 111, 1), "min_pts": min_pts},
        "total_civilizations": len(all_civs),
        "num_clusters": len([k for k in grouped if k != -1]),
        "noise_points": len(grouped.get(-1, [])),
        "clusters": grouped,
    }


@app.get("/api/compare")
def compare(
    a: str = Query(..., description="Name of civilization A"),
    b: str = Query(..., description="Name of civilization B"),
):
    civ_a = next((c for c in all_civs if c.name == a), None)
    civ_b = next((c for c in all_civs if c.name == b), None)
    if not civ_a:
        raise HTTPException(status_code=404, detail=f"Not found: {a}")
    if not civ_b:
        raise HTTPException(status_code=404, detail=f"Not found: {b}")

    dist = math.sqrt(
        (civ_a.latitude - civ_b.latitude) ** 2 +
        (civ_a.longitude - civ_b.longitude) ** 2
    ) * 111

    winner = civ_a.name if civ_a.spatial_score() >= civ_b.spatial_score() else civ_b.name
    return {
        "civilization_a": civ_a.to_dict(),
        "civilization_b": civ_b.to_dict(),
        "score_a": civ_a.spatial_score(),
        "score_b": civ_b.spatial_score(),
        "distance_km": round(dist, 2),
        "winner": winner,
    }


@app.get("/api/rtree")
def rtree_lookup(
    lat: float = Query(..., ge=-90,  le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    regions = r_tree.query_point(lat, lon)
    return {
        "query": {"lat": lat, "lon": lon},
        "regions": regions,
        "count": len(regions),
        "algorithm": "R-Tree bounding box overlap O(log n)",
    }


@app.get("/api/stats")
def stats():
    n = len(all_civs)
    log_n = math.ceil(math.log2(n)) if n > 0 else 0
    return {
        "total_civilizations": n,
        "kdtree_nodes": kd_tree.node_count,
        "rtree_regions": len(r_tree.regions),
        "linear_ops": n,
        "kdtree_ops": log_n,
        "speedup": n // log_n if log_n > 0 else 1,
    }


# ── Chat endpoint ───────────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: dict):
    raw_message = req.get("message", "").strip()
    message = raw_message.lower()

    if not raw_message:
        return {"response": "Please type a message and I will help you."}

    # Step 1: Smart local answers (instant, no API needed)
    if any(word in message for word in ("hello", "hi", "hey")):
        return {"response": "Hello! I'm your Spatial Intelligence Assistant. Ask me about civilizations, KD-Trees, the REST API, clustering, or anything about this project!"}
    elif "date" in message or "today" in message:
        return {"response": f"Today's date is {datetime.now().strftime('%d %B %Y')}."}
    elif "time" in message:
        return {"response": f"Current server time is {datetime.now().strftime('%I:%M %p')}."}

    # Step 2: Gemini with smart system prompt + longer timeout
    SYSTEM_PROMPT = """You are a Spatial Intelligence Assistant for the Civilization Mapper project.

PROJECT DETAILS:
- Full-stack app: C++ KD-Tree backend + FastAPI middleware + Leaflet map frontend
- Dataset: 47+ civilizations (Indian + global) with lat/lon, resource/knowledge/military scores
- Spatial Score = (Resource + Knowledge + Military) / 3
- Features: nearest-neighbor search, range queries, DBSCAN clustering, map visualization
- Frontend calls FastAPI REST API in real time on map click

KEY CIVILIZATIONS:
- Mughal Empire: (28.6N, 77.2E), South Asia, 1526-1857 CE, Score: 89.33
- Maurya Empire: (25.0N, 83.0E), South Asia, 322-185 BCE
- Gupta Empire: (24.5N, 82.5E), South Asia, 320-550 CE
- Chola Dynasty: (10.8N, 79.7E), South India, Score: 85.33
- Indus Valley: (27.0N, 68.0E), 3300-1300 BCE
- Han China: (35.0N, 105.0E), East Asia, 206 BCE-220 CE
- Persian Empire: (32.0N, 53.0E), Middle East, Score: 83.33
- Roman Empire, Greek, Ottoman, Aztec, Inca, Mali, Songhai also included

RULES:
- Answer questions about this project, civilizations, history, coding, or anything general
- Be concise but informative
- For civilization data questions, use the details above
- Never say you don't know basic facts
- Keep responses under 4 sentences unless detail is needed"""

    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model="gemini-2.0-flash",
                contents=raw_message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=500,
                )
            ),
            timeout=30,
        )

        if response and response.text:
            return {"response": response.text}

    except asyncio.TimeoutError:
        return {"response": f"Request timed out. Try again - Gemini is sometimes slow. (Your question: '{raw_message[:50]}')"}
    except Exception as e:
        pass

    # Step 3: Smart offline fallback (only if Gemini completely fails)
    if "kd-tree" in message or "kdtree" in message:
        return {"response": "KD-Tree is a spatial data structure for efficient nearest neighbor search with O(log n) average complexity. This project uses it to find the closest civilizations to any clicked point on the map."}
    elif "cluster" in message:
        return {"response": "Clustering uses DBSCAN, which groups nearby civilizations based on geographic density. Unlike K-Means, DBSCAN doesn't need a fixed number of clusters."}
    elif "mughal" in message:
        return {"response": "Mughal Empire: Located at (28.6 deg N, 77.2 deg E), South Asia. Period: 1526-1857 CE. Spatial Score: 89.33 (Resource: 90, Knowledge: 88, Military: 90)."}
    elif "maurya" in message:
        return {"response": "Maurya Empire: Located at (25.0 deg N, 83.0 deg E), South Asia. Period: 322-185 BCE. One of the largest empires in Indian history."}
    elif "gupta" in message:
        return {"response": "Gupta Empire: Located at (24.5 deg N, 82.5 deg E), South Asia. Period: 320-550 CE. Known as India's Golden Age - advances in science, math, and art."}
    elif "chola" in message:
        return {"response": "Chola Dynasty: Located at (10.8 deg N, 79.7 deg E), South India. Period: 300 BCE-1279 CE. Known for naval power and temple architecture."}
    elif "score" in message or "spatial" in message:
        return {"response": "Spatial Score = (Resource + Knowledge + Military) / 3. It ranks civilizations by their overall strength across three dimensions."}
    elif "api" in message or "rest" in message or "endpoint" in message:
        return {"response": "The backend exposes REST API endpoints via FastAPI: /api/nearest for KD-Tree neighbor search, /api/range for range queries, /api/cluster for DBSCAN clustering, and /api/civilizations for the full dataset."}
    elif "project" in message:
        return {"response": "This is a Civilization Spatial Mapper - a full-stack spatial intelligence system using C++ KD-Tree backend, FastAPI middleware, and an interactive Leaflet map frontend with 47+ civilizations."}
    elif "indian" in message or "india" in message:
        return {"response": "Indian civilizations in the dataset include: Indus Valley, Harappan, Vedic, Maurya, Gupta, Satavahana, Chola, Pallava, Pandya, Rashtrakuta, Vijayanagara, Delhi Sultanate, Mughal, Maratha, Sikh Empire, and more - spanning 3300 BCE to 1947 CE."}
    else:
        return {"response": "I'm your Spatial Intelligence Assistant. Ask me about civilizations in the dataset, KD-Tree algorithms, the REST API, clustering, or anything about this project!"}
