# 🗺️ Civilization Spatial Intelligence Mapper
**DSA Industry Project | KD-Trees · R-Trees · Multi-Dimensional Indexing**

---

## 📌 Problem Statement
Civilizations are traditionally compared philosophically or ethically — both subjective.  
This project compares them **purely on geography** using spatial data structures.

---

## 🏗️ Architecture

```
Data Ingestion Layer    → CSV Loader (civilizations.csv)
        ↓
Spatial Indexing Engine → KD-Tree (built from scratch) + R-Tree (bounding boxes)
        ↓
Query Engine            → Nearest Neighbor | Range Query | R-Tree Point Lookup
        ↓
Analysis Layer          → Comparative Analysis | Time Complexity Report
        ↓
Reporting Layer         → Console output + JSON export (for frontend)
```

---

## 🧠 DSA Concepts Used

| Concept | Where Used |
|---|---|
| Binary Trees | KD-Tree node structure |
| Recursion | KD-Tree insert, nearest neighbor, range query |
| Divide & Conquer | Axis-based splitting (lat/lon alternating) |
| Spatial Pruning | Branch skipping in nearest neighbor search |
| Multi-dim Indexing | 2D point indexing (latitude, longitude) |
| Bounding Boxes | R-Tree region overlap queries |

---

## ⏱️ Time Complexity

| Method | Complexity | Operations (n=15) |
|---|---|---|
| Linear Search | O(n) | 15 |
| KD-Tree (avg) | O(log n) | 4 |
| R-Tree Range | O(log n + k) | ~7 |

**KD-Tree is ~3–4x faster than linear search at n=15, and exponentially faster at scale.**

---

## 🚀 How to Compile & Run

### Option 1 — Using Make (recommended)
```bash
make        # compile
make run    # compile + run
make clean  # remove binary
```

### Option 2 — Direct g++ command
```bash
g++ -std=c++17 -Wall -O2 -o civilization_mapper civilization_mapper.cpp
./civilization_mapper
```

> ✅ Tested with: g++ 13.x on Ubuntu / g++ 12.x on Windows (MinGW)

---

## 📂 Files

```
civilization_mapper.cpp   → Full C++ source (KD-Tree, R-Tree, queries)
civilizations.csv         → Dataset (15 civilizations, can add more)
Makefile                  → One-command build
civilization_mapper_frontend.html → Interactive browser UI (open in Chrome)
README.md                 → This file
```

---

## 🔎 Queries Supported

1. **Nearest Neighbor** — "Which civilization existed closest to (30°N, 70°E)?"
2. **Range Query** — "Find all civilizations in Lat[20–40], Lon[25–90]"
3. **R-Tree Point Lookup** — "Which region does (25°N, 75°E) fall in?"
4. **Comparative Analysis** — Compare any two civilizations spatially

---

## 📊 Sample Output
```
✅ Data Ingestion Complete: 15 civilizations loaded.
✅ KD-Tree Built: 15 nodes indexed.

🔎 Nearest to (30.0, 70.0) → Indus Valley [23.5, 68.4] | Score: 75.67
🔎 Range Lat[20-40] Lon[25-90] → 7 civilizations found
🏆 Comparative: Ancient Egypt (79.67) > Indus Valley (75.67)
🚀 KD-Tree is ~3x faster than linear search!
```

---

## 👩‍💻 Team
Industry Project — DSA Subject  
Technology: C++17 | KD-Trees | R-Trees | Spatial Indexing
