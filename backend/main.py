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
import httpx
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from models import Civilization, ClusterResult
from kdtree import KDTree
from rtree_index import RTreeIndex
from loader import load_civilizations
from clustering import dbscan

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

print(f"✅ Loaded {len(all_civs)} civilizations")
print(f"✅ KD-Tree built: {kd_tree.node_count} nodes")
print(f"✅ R-Tree built:  {len(r_tree.regions)} regions")


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

class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    api_key: str = ""

CHAT_SYSTEM = """You are the Spatial Intelligence Assistant for the "Civilization Spatial Intelligence Mapper" project.

PROJECT CONTEXT:
- A spatial data system indexing historical civilizations by latitude, longitude, and time
- C++ core: KD-Tree (insertion, nearest neighbor O(log n), range search O(log n+k)), R-Tree (bounding box regions)
- FastAPI Python backend exposing: /run, /api/civilizations, /api/nearest, /api/range, /api/cluster, /api/compare, /api/rtree, /api/stats
- DBSCAN clustering built on top of KD-Tree range search (no external libraries)
- Leaflet.js frontend with CARTO Dark tiles, live map click queries
- Dataset: 47 Indian civilizations from final_dataset.csv

You are a general-purpose AI assistant. You can answer ANY question — about this project, history, geography, programming, algorithms, data structures, or any other topic. When questions relate to the project, give specific technical answers. For general questions, answer helpfully and thoroughly.

Be concise, friendly, and technically accurate."""


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Proxy chat requests to Anthropic Claude.
    Accepts an api_key in the request body so the frontend never stores it server-side.
    Falls back to ANTHROPIC_API_KEY env var if no key provided in request.
    """
    api_key = req.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="No API key provided. Pass api_key in request body or set ANTHROPIC_API_KEY env var.",
        )

    messages = [{"role": m.role, "content": m.content} for m in req.history]
    messages.append({"role": "user", "content": req.message})

    payload = {
        "model": "claude-3-5-sonnet-latest",
        "max_tokens": 1024,
        "system": CHAT_SYSTEM,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                    "x-api-key": api_key,
                },
            )
        if resp.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid Anthropic API key")
        if not resp.is_success:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

        data = resp.json()
        reply = data["content"][0]["text"]
        return {"reply": reply}

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Anthropic API timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
