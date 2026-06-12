# Civilization Spatial Intelligence Mapper 🌍

Welcome to the **Civilization Spatial Intelligence Mapper**, an interactive, full-stack web application designed to map and query historical civilizations and dynasties across the globe (with a special emphasis on Indian history). The project leverages advanced spatial data structures like KD-Trees and R-Trees to provide lightning-fast geographic queries, nearest neighbor searches, and regional data clustering.

---

## 🚀 Features

- **Interactive Leaflet Map**: Visualize civilizations on a high-performance CARTO Dark map. Clicking anywhere on the map triggers a real-time nearest-neighbor search.
- **Advanced Spatial Query Engine**:
  - **KD-Tree Nearest Neighbor**: Instantly find the closest civilization to any latitude/longitude coordinate.
  - **KD-Tree Range Query**: Select a bounding box (min/max coordinates) to find all civilizations within that specific region.
  - **R-Tree Region Lookup**: Fast bounded region indexing.
- **User Authentication**: Secure Login, Signup, and password reset functionality backed by PostgreSQL.
- **Dynamic User Profiles**: Users can view their personally uploaded dynasties ("My Posts") and update their passwords.
- **Live Data Entry & Deletion**: Add custom civilizations directly from the UI to the database, which dynamically rebuilds the KD-Tree in real-time. Deletion of custom and built-in civilizations is also supported with immediate map updates.
- **Interactive UI Components**: Includes a Civilization-Region Matrix Table with instant search filtering, an Action column with a quick delete `✕` button, a Regional Heat Map, and a dynamic KD-Tree visualizer canvas.

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
- **PostgreSQL**: Relational database storing user accounts, built-in civilizations, and custom civilizations.

### Core Algorithms (Implemented in Python & C++)
- **KD-Tree (`backend/kdtree.py`)**: For ultra-fast nearest neighbor spatial lookups.
- **R-Tree (`backend/rtree_index.py`)**: For spatial bounding box queries.
- **DBSCAN Clustering (`backend/clustering.py`)**: Density-based spatial clustering of applications with noise.
- **C++ Spatial Engine (`civilization_mapper.cpp`)**: High-performance core compiled to `mapper.exe` for standalone spatial benchmarking.

---

## 📁 File Structure

```text
civilization-spatial-mapper/
│
├── civilization_mapper_frontend.html  # The main application UI (Frontend).
├── civilization_mapper.cpp            # C++ spatial query engine.
├── httplib.h                          # C++ httplib header.
├── Makefile                           # Makefile for compiling the C++ engine.
├── mapper.exe                         # Compiled C++ spatial engine binary.
├── run_app.bat                        # Batch script to auto-install dependencies, start the backend, and open the UI.
├── README.md                          # Project documentation.
│
└── backend/                           # Python FastAPI Backend
    ├── main.py                        # The primary FastAPI server and API endpoints (login, query, civilizations).
    ├── database.py                    # PostgreSQL client integration (auth, data operations).
    ├── models.py                      # Data structures and Pydantic models for the API.
    ├── kdtree.py                      # KD-Tree spatial algorithm implementation in Python.
    ├── rtree_index.py                 # R-Tree bounding box algorithm implementation in Python.
    ├── clustering.py                  # DBSCAN algorithm for spatial data clustering.
    ├── requirements.txt               # Python package dependencies.
    └── .env                           # Environment configuration file.
```

---

## ⚙️ How It Works

1. **Initialization**: When the backend server boots (`main.py`), it connects to PostgreSQL via `database.py`. It pulls all global civilizations and user-submitted custom civilizations directly from the database.
2. **Tree Building**: The backend processes the coordinate data to build a balanced, optimized KD-Tree in memory.
3. **Frontend Communication**: The frontend (`civilization_mapper_frontend.html`) communicates asynchronously with the FastAPI server via REST endpoints (e.g., `/api/civilizations`, `/api/nearest`).
4. **Spatial Searching**: When a user clicks the map, the frontend sends the click coordinates to the `/api/nearest` backend endpoint. The Python backend traverses the KD-Tree, returning the geographically closest civilization.
5. **Data Integration**: If an authenticated user adds or deletes a civilization through the web UI, the backend commits the change to the PostgreSQL database and automatically rebuilds the in-memory KD-Tree to keep the spatial index in sync.

---

## ⚙️ How to Install & Setup

Follow these steps to set up and run the project locally on your machine:

### 1. Prerequisites
- **Python 3.10+**: Ensure Python is installed and added to your system's PATH.
- **PostgreSQL**: Install PostgreSQL server locally or use a remote instance.

### 2. Database Setup
1. Log in to your PostgreSQL instance (via pgAdmin, psql, or command line).
2. Create a new database named `civilization_mapper`:
   ```sql
   CREATE DATABASE civilization_mapper;
   ```
   *Note: The backend will automatically create the required tables (`users`, `civilizations`, `custom_civilizations`) and seed the 59 civilizations on its first boot! No manual table setup is required.*

### 3. Environment Configuration
1. Navigate to the `backend/` directory.
2. Create a new file named `.env` (you can copy `.env.example` as a template).
3. Fill in the following credentials:
   ```env
   # PostgreSQL Connection URL
   DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/civilization_mapper

   # OpenAI Key (For the AI assistant chatbot)
   OPENAI_API_KEY=sk-proj-...

   # SMTP settings for sending password reset emails
   GMAIL_SENDER=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-gmail-app-password
   ```

### 4. Running the Application
#### Option A: Quick Start (Windows)
Simply double-click the **`run_app.bat`** file in the root folder. This batch script will automatically:
1. Verify/install missing Python packages from `requirements.txt`.
2. Spin up the FastAPI backend on port `8080`.
3. Open the application frontend directly in your default browser.

#### Option B: Manual Startup (All Platforms)
1. Open a terminal in the project root directory and navigate to `backend`:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the FastAPI development server:
   ```bash
   uvicorn main:app --reload --port 8080
   ```
4. Access the web interface by visiting `http://localhost:8080` in your web browser.
