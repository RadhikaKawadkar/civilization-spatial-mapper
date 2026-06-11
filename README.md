# Civilization Spatial Intelligence Mapper 🌍

Welcome to the **Civilization Spatial Intelligence Mapper**, an interactive, full-stack web application designed to map and query historical civilizations and dynasties across the globe (with a special emphasis on Indian history). The project leverages advanced spatial data structures like KD-Trees and R-Trees to provide lightning-fast geographic queries, nearest neighbor searches, and regional data clustering.

---

## 🚀 Features

- **Interactive Leaflet Map**: Visualize civilizations on a high-performance CARTO Dark map. Clicking anywhere on the map triggers a real-time nearest-neighbor search.
- **Advanced Spatial Query Engine**:
  - **KD-Tree Nearest Neighbor**: Instantly find the closest civilization to any latitude/longitude coordinate.
  - **KD-Tree Range Query**: Select a bounding box (min/max coordinates) to find all civilizations within that specific region.
  - **R-Tree Region Lookup**: Fast bounded region indexing.
- **User Authentication**: Secure Login and Signup functionality backed by Supabase.
- **Dynamic User Profiles**: Users can view their personally uploaded dynasties ("My Posts") and update their passwords.
- **Live Data Entry**: Add custom civilizations directly from the UI to the cloud database, which dynamically rebuilds the KD-Tree in real-time.
- **Interactive UI Components**: Includes a Civilization-Region Matrix Table with instant search filtering, a Regional Heat Map, and a dynamic KD-Tree visualizer canvas.

---

## 🛠️ Tech Stack

### Frontend
- **HTML5 / CSS3 / Vanilla JavaScript**: A completely custom, lightweight, framework-free frontend built for maximum performance.
- **Leaflet.js**: An open-source JavaScript library for interactive maps, using beautifully styled CARTO Dark map tiles.
- **Custom UI System**: Glassmorphism effects, rich gold/dark themes, and interactive animations.

### Backend
- **Python 3**: The core programming language for the backend server and spatial logic.
- **FastAPI**: A modern, high-performance web framework used to build the RESTful API.
- **Uvicorn**: An ASGI web server implementation for Python.

### Database & Storage
- **Supabase (PostgreSQL)**: The cloud-native relational database. All user accounts and civilization data are securely stored and queried directly from the cloud.

### Core Algorithms (Implemented in Python)
- **KD-Tree (`kdtree.py`)**: For ultra-fast nearest neighbor spatial lookups.
- **R-Tree (`rtree_index.py`)**: For spatial bounding box queries.
- **DBSCAN Clustering (`clustering.py`)**: Density-based spatial clustering of applications with noise.

---

## 📁 File Structure

```text
civilization-spatial-mapper/
│
├── civilization_mapper_frontend.html  # The main application UI (Frontend).
├── run_app.bat                        # Batch script to auto-install dependencies, start the backend, and open the UI.
├── supabase_schema.sql                # SQL initialization script used to set up the Supabase database tables.
├── README.md                          # Project documentation.
│
└── backend/                           # Python FastAPI Backend
    ├── main.py                        # The primary FastAPI server and API endpoints (login, query, civilizations).
    ├── database.py                    # Supabase client integration (auth, data fetching, password updates).
    ├── models.py                      # Data structures and Pydantic models for the API.
    ├── kdtree.py                      # KD-Tree spatial algorithm implementation.
    ├── rtree_index.py                 # R-Tree bounding box algorithm implementation.
    ├── clustering.py                  # DBSCAN algorithm for spatial data clustering.
    ├── transfer_data.py               # Utility script used previously to migrate local CSV data to Supabase cloud.
    ├── requirements.txt               # Python package dependencies (fastapi, supabase, pydantic, etc.).
    └── .env                           # Environment file containing SUPABASE_URL and SUPABASE_KEY.
```

---

## ⚙️ How It Works

1. **Initialization**: When the backend server boots (`main.py`), it establishes a connection to Supabase via `database.py`. It pulls all global civilizations and user-submitted custom civilizations directly from the cloud database.
2. **Tree Building**: The backend immediately processes the raw coordinate data to build a highly optimized KD-Tree in memory.
3. **Frontend Communication**: The frontend (`civilization_mapper_frontend.html`) communicates asynchronously with the FastAPI server via REST endpoints (e.g., `/api/civilizations`, `/api/nearest`).
4. **Spatial Searching**: When a user clicks the map, the frontend sends the click coordinates to the `/api/nearest` backend endpoint. The Python backend traverses the KD-Tree, instantly returning the geographically closest civilization.
5. **Data Integration**: If an authenticated user adds a new civilization through the web UI, the backend commits it to the Supabase database and automatically dynamically re-balances the in-memory KD-Tree to include the new point without requiring a server restart.

---

## 🏁 Getting Started

1. **Prerequisites**: Ensure you have **Python 3** installed on your system.
2. **Environment Setup**: Ensure your `backend/.env` file is properly configured with your Supabase credentials (`SUPABASE_URL` and `SUPABASE_KEY`).
3. **Run the Project**: Simply double-click the **`run_app.bat`** file. 
   - This script will automatically install missing Python libraries.
   - It will launch the FastAPI backend server on port `8080`.
   - It will automatically open `civilization_mapper_frontend.html` in your default web browser.
