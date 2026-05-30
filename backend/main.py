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
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from models import Civilization, ClusterResult
from kdtree import KDTree
from rtree_index import RTreeIndex
from clustering import dbscan
from database import init_db, create_user, get_user_by_email, get_user_by_id, add_custom_civilization, get_custom_civilizations, update_user_password, get_civilizations_by_user
import hashlib

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

CPP_EXE  = Path(__file__).parent.parent / "mapper.exe"

init_db()

all_civs: list[Civilization] = []

custom_rows = get_custom_civilizations()
for row in custom_rows:
    c = Civilization(
        name=row["name"], lat=row["lat"], lon=row["lon"],
        start=row.get("start_year") or 0, end=row.get("end_year") or 0, region=row.get("region") or "Unknown",
        resource=row.get("resource_density") or 50.0, knowledge=row.get("knowledge_density") or 50.0,
        military=row.get("military_strength") or 50.0, added_by_name=row.get("added_by_name")
    )
    all_civs.append(c)

kd_tree = KDTree()
kd_tree.build(all_civs)

r_tree = RTreeIndex()
r_tree.add_default_regions()

print(f"[OK] Loaded {len(all_civs)} civilizations")
print(f"[OK] KD-Tree built: {kd_tree.node_count} nodes")
print(f"[OK] R-Tree built:  {len(r_tree.regions)} regions")


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

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/register")
def register(req: RegisterRequest):
    user_id = create_user(req.name, req.email, req.password)
    if not user_id:
        raise HTTPException(status_code=400, detail="Email already registered")
    return {"message": "User created", "user_id": user_id, "name": req.name}

@app.post("/api/login")
def login(req: LoginRequest):
    user = get_user_by_email(req.email)
    if not user or user["password_hash"] != hashlib.sha256(req.password.encode()).hexdigest():
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Login successful", "token": user["id"], "name": user["name"]}

class ChangePasswordRequest(BaseModel):
    token: int
    old_password: str
    new_password: str

@app.post("/api/change-password")
def change_password(req: ChangePasswordRequest):
    user = get_user_by_id(req.token)
    if not user or user["password_hash"] != hashlib.sha256(req.old_password.encode()).hexdigest():
        raise HTTPException(status_code=401, detail="Invalid current password")
    
    success = update_user_password(user["id"], req.new_password)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")
    return {"message": "Password updated successfully"}

@app.get("/api/user-civilizations")
def get_user_civilizations(token: int = Query(...)):
    user = get_user_by_id(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_civs = get_civilizations_by_user(token)
    return user_civs

class CivilizationRequest(BaseModel):
    name: str
    lat: float
    lon: float
    region: str
    resource: float
    knowledge: float
    military: float
    token: int

@app.post("/api/civilizations")
def post_civilization(req: CivilizationRequest):
    user = get_user_by_id(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    civ_id = add_custom_civilization(
        req.name, req.lat, req.lon, req.region,
        req.resource, req.knowledge, req.military, user["id"]
    )
    if not civ_id:
        raise HTTPException(status_code=400, detail="Civilization name already exists")
    
    c = Civilization(
        name=req.name, lat=req.lat, lon=req.lon,
        region=req.region, resource=req.resource, knowledge=req.knowledge,
        military=req.military, added_by_name=user["name"]
    )
    all_civs.append(c)
    kd_tree.build(all_civs)
    return {"message": "Civilization added", "civilization": c.to_dict()}

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


# ── Chat endpoint (Gemini) ──────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

class ChatResponse(BaseModel):
    reply: str
    ok: bool = True
    model: str | None = None
    error: str | None = None

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
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Proxy chat requests to Gemini API (key stored server-side).

    Frontend sends only the user message + (optional) short history.
    The Gemini API key is read from GEMINI_API_KEY env var (via .env).
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash").strip() or "gemini-1.5-flash"

    if not req.message or not req.message.strip():
        return ChatResponse(reply="Please type a message.", ok=False, model=model, error="empty_message")

    if not api_key:
        # Don't crash the frontend—return a friendly message instead.
        return ChatResponse(
            reply=(
                "Chat is not configured yet. Set `GEMINI_API_KEY` in `backend/.env` and restart the backend.\n\n"
                "Tip: You can still use the UI—project suggestions will work even without AI."
            ),
            ok=False,
            model=model,
            error="missing_api_key",
        )

    # Add lightweight live context (kept short to reduce tokens)
    try:
        region_set = sorted({(c.region or "Unknown").strip() for c in all_civs})
        ctx = (
            f"Live dataset: {len(all_civs)} civilizations across {len(region_set)} region(s): "
            + ", ".join(region_set[:12])
            + ("..." if len(region_set) > 12 else "")
            + f". KD-Tree nodes: {kd_tree.node_count}. R-Tree regions indexed: {len(r_tree.regions)}."
        )
    except Exception:
        ctx = "Live dataset loaded. (Context unavailable.)"

    system = CHAT_SYSTEM + "\n\nLIVE CONTEXT:\n" + ctx

    # Format history for Gemini
    gemini_messages = []
    for m in req.history:
        role = "user" if m.role == "user" else "model"
        gemini_messages.append({"role": role, "parts": [{"text": m.content}]})
    gemini_messages.append({"role": "user", "parts": [{"text": req.message}]})

    payload = {
        "systemInstruction": {
            "parts": [{"text": system}]
        },
        "contents": gemini_messages
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        
        if not resp.is_success:
            if resp.status_code == 400 and "API key not valid" in resp.text:
                raise HTTPException(status_code=401, detail="Invalid Gemini API key")
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

        data = resp.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            reply = "I'm sorry, I couldn't generate a response."
            
        return ChatResponse(reply=reply, ok=True, model=model)

    except httpx.TimeoutException:
        return ChatResponse(reply="The AI service timed out. Please try again.", ok=False, model=model, error="timeout")
    except HTTPException:
        raise
    except Exception as e:
        # Surface a stable error response so the UI can show a friendly message.
        return ChatResponse(
            reply="I couldn’t reach the AI service right now. Please try again in a moment.",
            ok=False,
            model=model,
            error=str(e)[:200],
        )
