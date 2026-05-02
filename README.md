# Civilization Spatial Intelligence Mapper

A spatial data system that indexes historical civilizations by latitude, longitude, and time using KD-Trees and R-Trees. Exposes a FastAPI REST backend and a Leaflet.js map frontend.

---

## Problem Statement

Historical civilizations are inherently spatial — they rise and fall at specific coordinates over time. Standard databases answer "find civilization by name", but spatial questions like "which civilizations existed within 500 km of Rome?" or "which clusters of civilizations share the same geographic region?" require spatial indexing structures.

This project implements those structures from scratch (KD-Tree in C++, mirrored in Python) and wraps them in a production-style REST API.

---

## Architecture

```
┌─────────────────────────────────────┐
│   Frontend (civilization_mapper_    │
│   frontend.html — Leaflet.js)       │
└────────────────┬────────────────────┘
                 │ HTTP fetch()
┌────────────────▼────────────────────┐
│   FastAPI Backend  (backend/)       │
│                                     │
│   /run        → subprocess C++ exe │
│   /api/nearest → KD-Tree NN        │
│   /api/range   → KD-Tree range     │
│   /api/cluster → DBSCAN            │
│   /api/compare → score comparison  │
│   /api/rtree   → R-Tree regions    │
│   /api/stats   → tree metrics      │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   C++ Spatial Engine  (core/)       │
│   KD-Tree + R-Tree (mapper.exe)     │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Data  (data/final_dataset.csv)    │
│   47 civilizations, lat/lon/time    │
└─────────────────────────────────────┘
```

---

## Project Structure

```
.
├── backend/
│   ├── main.py          # FastAPI app — all endpoints
│   ├── models.py        # Civilization + ClusterResult dataclasses
│   ├── kdtree.py        # KD-Tree (build, nearest, range, neighbors_within)
│   ├── rtree_index.py   # R-Tree bounding box regions
│   ├── clustering.py    # DBSCAN using KD-Tree range search
│   ├── loader.py        # CSV loader (supports both CSV formats)
│   └── requirements.txt
├── core/
│   ├── kd_tree.cpp / .h
│   └── rtree/rtree.cpp / .h
├── data/
│   ├── final_dataset.csv   # 47 Indian civilizations
│   └── csv_loader.cpp / .h
├── analytics/
│   ├── benchmark.cpp / .h
│   └── spatial_scaling_test.cpp
├── utils/logger.cpp / .h
├── main.cpp                # C++ console entry point
├── CMakeLists.txt
├── Makefile
└── civilization_mapper_frontend.html
```

---

## How to Run

### 1. Start the FastAPI backend

```bash
cd backend
uvicorn main:app --reload --port 8080
```

The API will be live at `http://localhost:8080`.  
Interactive docs: `http://localhost:8080/docs`

### 2. Open the frontend

Open `civilization_mapper_frontend.html` directly in Chrome/Firefox.  
It connects to `http://localhost:8080` automatically.

### 3. Build and run the C++ engine (optional)

```bash
# Windows (MinGW)
mingw32-make

# Linux / macOS
make

# Run standalone
./mapper.exe
```

The `/run` endpoint executes `mapper.exe` via subprocess and returns its output.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/run` | Execute C++ engine, return stdout |
| GET | `/api/civilizations` | All civilizations |
| GET | `/api/nearest?lat=&lon=` | KD-Tree nearest neighbor |
| GET | `/api/range?latMin=&latMax=&lonMin=&lonMax=` | KD-Tree range query |
| GET | `/api/cluster?eps=&min_pts=` | DBSCAN geographic clustering |
| GET | `/api/compare?a=&b=` | Compare two civilizations by score |
| GET | `/api/rtree?lat=&lon=` | R-Tree region lookup |
| GET | `/api/stats` | Tree node counts and speedup metrics |

### Example calls

```bash
# Nearest civilization to central India
curl "http://localhost:8080/api/nearest?lat=20&lon=78"

# All civilizations in South Asia bounding box
curl "http://localhost:8080/api/range?latMin=8&latMax=35&lonMin=60&lonMax=97"

# DBSCAN clusters with 10-degree radius, min 2 points
curl "http://localhost:8080/api/cluster?eps=10&min_pts=2"

# Execute C++ engine
curl "http://localhost:8080/run"
```

---

## Algorithms

**KD-Tree** — alternates split axis (latitude / longitude) at each depth level.  
- Nearest neighbor: O(log n) average with branch pruning  
- Range query: O(log n + k) where k = results returned  

**DBSCAN** — density-based clustering, no cluster count needed.  
- Uses `kdtree.neighbors_within(lat, lon, eps)` as the ε-neighborhood query  
- Discovers geographic hotspots (Gangetic Plain, Deccan, Mediterranean) automatically  
- Points with fewer than `min_pts` neighbors are labeled noise (-1)  

**R-Tree** — 8 named bounding box regions for continent-level lookups.  
- Point-in-region: O(regions) — constant for fixed region count  

---

## Dependencies

- Python 3.10+
- `fastapi==0.115.14`
- `uvicorn==0.35.0`
- C++17 compiler (for the optional C++ engine)
