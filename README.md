# 🗺️ Civilization Spatial Intelligence Mapper

**DSA Industry Project | KD-Trees · R-Trees · Multi-Dimensional Indexing**

> A spatial intelligence engine that compares civilizations based on geography using KD-Trees and multi-dimensional indexing, enabling efficient region and proximity queries at O(log n) average time complexity.

---

## 🚀 Live Demo

Open `civilization_mapper_frontend.html` directly in any browser — no server required.

---

## 📁 Project Structure

```
civilization-spatial-mapper/
├── civilization_mapper.cpp          ← C++ backend (KD-Tree, R-Tree, queries)
├── civilization_mapper_frontend.html ← Interactive frontend (Leaflet.js map + AI assistant)
├── civilizations.csv                ← Dataset (27 civilizations)
└── README.md
```

---

## ⚙️ How to Run the C++ Backend

**Requirements:** g++ with C++17 support

```bash
# Compile
g++ -std=c++17 -o civilization_mapper civilization_mapper.cpp

# Run
./civilization_mapper          # Linux / Mac
civilization_mapper.exe        # Windows
```

**Expected output:**
- KD-Tree inorder traversal (27 nodes)
- Nearest Neighbor Query result
- Range Query results
- Comparative Analysis (Indus Valley vs Ancient Egypt)
- Time Complexity Analysis table
- Exports `civilizations_data.json` for frontend

---

## 🌍 How to Use the Frontend

1. Open `civilization_mapper_frontend.html` in Chrome, Firefox, or Edge
2. The map loads centered on India with all 27 civilization markers
3. **Click anywhere on the map** → runs a KD-Tree nearest-neighbor query
4. Use the **Query Engine** panel for nearest neighbor, range, compare, and R-Tree queries
5. Use **Add Civilization** to insert new data points into the KD-Tree (saved to browser storage)
6. Click **Export CSV** to sync new civilizations to the C++ backend

---

## 🧠 DSA Concepts Implemented

| Concept | Implementation |
|---|---|
| KD-Tree | Built from scratch in C++ — recursive insertion, axis-based splitting |
| Nearest Neighbor Search | O(log n) with branch pruning |
| Range Query | O(log n + k) spatial bounding box search |
| R-Tree | Bounding box regional index (8 geographic regions) |
| Divide & Conquer | Median-based balanced tree construction |
| Multi-dimensional Indexing | 2D spatial indexing (latitude × longitude) |

### Time Complexity

| Operation | Average | Worst |
|---|---|---|
| KD-Tree Insert | O(log n) | O(n) |
| Nearest Neighbor | O(log n) | O(n) |
| Range Query | O(log n + k) | O(n) |
| Linear Search | O(n) | O(n) |

---

## 🇮🇳 Indian Civilizations Dataset (15 civilizations)

| Civilization | Period | Region |
|---|---|---|
| Indus Valley | 3300–1300 BCE | South Asia |
| Vedic India | 1500–600 BCE | South Asia |
| Maurya Empire | 322–185 BCE | South Asia |
| Gupta Empire | 320–550 CE | South Asia |
| Chola Dynasty | 300–1279 CE | South India |
| Vijayanagara | 1336–1646 CE | South India |
| Maratha Empire | 1674–1818 CE | South Asia |
| Delhi Sultanate | 1206–1526 CE | South Asia |
| Mughal Empire | 1526–1857 CE | South Asia |
| Pallava Dynasty | 275–897 CE | South India |
| Satavahana | 230 BCE–220 CE | South Asia |
| Kushana Empire | 30–375 CE | Central Asia |
| Rashtrakuta | 753–982 CE | South India |
| Pala Empire | 750–1161 CE | South Asia |
| Chera Kingdom | 300 BCE–1102 CE | South India |

---

## 🏗️ System Architecture

```
Data Ingestion Layer       → CSV Loader (civilizations.csv)
        ↓
Spatial Indexing Engine    → KD-Tree (point queries)
                           → R-Tree  (region queries)
        ↓
Query Engine               → Nearest Neighbor  O(log n)
                           → Range Query       O(log n + k)
                           → Comparative Analysis
        ↓
Analysis Layer             → Complexity comparison (KD-Tree vs Linear)
        ↓
Visualization Layer        → C++ console output
                           → HTML/JS Leaflet.js frontend
                           → AI Chat Assistant (Claude API)
```

---

## 🗺️ Frontend Features

- **Real world map** — Leaflet.js with CARTO Dark tiles (no API key needed)
- **27 civilization markers** — Orange = Indian, Blue = Global, with popup bar charts
- **Click-to-query** — Click anywhere to run nearest-neighbor search
- **Range query rectangle** — Visualized on the map
- **Compare line** — Draws a line between two compared civilizations
- **🇮🇳 Focus India** button — Zooms to Indian subcontinent
- **AI Assistant** — Bottom-right chat popup powered by Claude API
- **localStorage persistence** — Added civilizations survive page refresh
- **Export CSV** — Syncs frontend data back to C++ backend

---

## 👥 Team

**Project:** Civilization Spatial Intelligence Mapper  
**Technology:** C++17, HTML/CSS/JavaScript, Leaflet.js  
**DSA Focus:** KD-Trees, R-Trees, Multi-Dimensional Spatial Indexing

---

## 📚 References

- Bentley, J.L. (1975). *Multidimensional binary search trees used for associative searching*
- Guttman, A. (1984). *R-Trees: A Dynamic Index Structure for Spatial Searching*
- Leaflet.js — [leafletjs.com](https://leafletjs.com)
- CARTO Map Tiles — [carto.com](https://carto.com)
