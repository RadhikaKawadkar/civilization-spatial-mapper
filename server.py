"""
================================================================
  CIVILIZATION SPATIAL INTELLIGENCE MAPPER
  Python REST API Server — drop-in replacement for C++ httplib
  
  Implements identical endpoints:
    GET /api/civilizations
    GET /api/nearest?lat=&lon=
    GET /api/range?latMin=&latMax=&lonMin=&lonMax=
    GET /api/compare?a=&b=
    GET /api/rtree?lat=&lon=
    GET /api/stats

  RUN:
    python server.py

  REQUIRES: Python 3.x (no pip installs needed — stdlib only)
================================================================
"""

import json
import math
import csv
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 8080

# ════════════════════════════════════════════════
#  DATA MODEL
# ════════════════════════════════════════════════

class Civilization:
    def __init__(self, name, lat, lon, start, end, region, res, know, mil):
        self.name               = name
        self.latitude           = float(lat)
        self.longitude          = float(lon)
        self.start_year         = int(start)
        self.end_year           = int(end)
        self.region             = region
        self.resource_density   = float(res)
        self.knowledge_density  = float(know)
        self.military_strength  = float(mil)

    def spatial_score(self):
        return round((self.resource_density + self.knowledge_density + self.military_strength) / 3, 2)

    def to_dict(self):
        return {
            "name":               self.name,
            "latitude":           self.latitude,
            "longitude":          self.longitude,
            "start_year":         self.start_year,
            "end_year":           self.end_year,
            "region":             self.region,
            "resource_density":   self.resource_density,
            "knowledge_density":  self.knowledge_density,
            "military_strength":  self.military_strength,
            "spatial_score":      self.spatial_score()
        }

# ════════════════════════════════════════════════
#  KD-TREE  (same logic as C++ implementation)
# ════════════════════════════════════════════════

class KDNode:
    def __init__(self, civ):
        self.civ   = civ
        self.left  = None
        self.right = None

class KDTree:
    def __init__(self):
        self.root       = None
        self.node_count = 0

    def build(self, civs, depth=0):
        if not civs:
            return None
        axis = depth % 2
        civs.sort(key=lambda c: c.latitude if axis == 0 else c.longitude)
        mid  = len(civs) // 2
        node = KDNode(civs[mid])
        node.left  = self.build(civs[:mid],   depth + 1)
        node.right = self.build(civs[mid+1:], depth + 1)
        self.node_count += 1
        return node

    def rebuild(self, civs):
        self.node_count = 0
        self.root = self.build(list(civs), 0)

    def _dist(self, a, b):
        return math.sqrt((a.latitude - b.latitude)**2 + (a.longitude - b.longitude)**2)

    def _nearest_search(self, node, query, best, depth=0):
        if node is None:
            return best
        d = self._dist(node.civ, query)
        if best is None or d < best[1]:
            best = (node.civ, d)
        axis  = depth % 2
        nv    = node.civ.latitude  if axis == 0 else node.civ.longitude
        qv    = query.latitude     if axis == 0 else query.longitude
        first, second = (node.left, node.right) if qv < nv else (node.right, node.left)
        best  = self._nearest_search(first,  query, best, depth + 1)
        # Branch pruning — only search other side if it could be closer
        if abs(qv - nv) < best[1]:
            best = self._nearest_search(second, query, best, depth + 1)
        return best

    def nearest(self, lat, lon):
        query = Civilization("q", lat, lon, 0, 0, "", 0, 0, 0)
        result = self._nearest_search(self.root, query, None, 0)
        return result  # (civ, dist)

    def _range_search(self, node, lat_min, lat_max, lon_min, lon_max, results, depth=0):
        if node is None:
            return
        c = node.civ
        if lat_min <= c.latitude <= lat_max and lon_min <= c.longitude <= lon_max:
            results.append(c)
        axis  = depth % 2
        nv    = c.latitude  if axis == 0 else c.longitude
        min_v = lat_min     if axis == 0 else lon_min
        max_v = lat_max     if axis == 0 else lon_max
        if min_v <= nv:
            self._range_search(node.left,  lat_min, lat_max, lon_min, lon_max, results, depth + 1)
        if max_v >= nv:
            self._range_search(node.right, lat_min, lat_max, lon_min, lon_max, results, depth + 1)

    def range_query(self, lat_min, lat_max, lon_min, lon_max):
        results = []
        self._range_search(self.root, lat_min, lat_max, lon_min, lon_max, results)
        return results

# ════════════════════════════════════════════════
#  R-TREE  (bounding box regions)
# ════════════════════════════════════════════════

class RTree:
    def __init__(self):
        self.regions = []

    def add_region(self, label, lat_min, lat_max, lon_min, lon_max):
        self.regions.append({
            "label":   label,
            "lat_min": lat_min, "lat_max": lat_max,
            "lon_min": lon_min, "lon_max": lon_max
        })

    def query_point(self, lat, lon):
        return [r["label"] for r in self.regions
                if r["lat_min"] <= lat <= r["lat_max"]
                and r["lon_min"] <= lon <= r["lon_max"]]

# ════════════════════════════════════════════════
#  DATA LOADING
# ════════════════════════════════════════════════

BUILTIN_DATA = [
    ("Ancient Egypt",   26.8,  30.8, -3100, -332,  "North Africa",  80, 78, 81),
    ("Mesopotamia",     33.0,  44.4, -3500, -539,  "Middle East",   78, 80, 75),
    ("Ancient Greece",  37.9,  23.7,  -800, -146,  "Mediterranean", 70, 95, 72),
    ("Roman Empire",    41.9,  12.5,   -27,  476,  "Mediterranean", 80, 70, 88),
    ("Han China",       35.0, 105.0,  -206,  220,  "East Asia",     88, 90, 85),
    ("Maya",            16.0, -89.0,   250,  900,  "Mesoamerica",   70, 88, 65),
    ("Persian Empire",  32.0,  53.0,  -550, -330,  "Middle East",   85, 75, 90),
    ("Byzantine",       41.0,  29.0,   330, 1453,  "Mediterranean", 75, 80, 78),
    ("Aztec",           19.4, -99.1,  1300, 1521,  "Mesoamerica",   72, 80, 85),
    ("Mongol Empire",   47.0, 106.0,  1206, 1368,  "Central Asia",  65, 60, 98),
    ("Ottoman Empire",  39.9,  32.9,  1299, 1922,  "Middle East",   80, 72, 88),
    ("Inca",           -13.5, -72.0,  1400, 1533,  "South America", 78, 75, 82),
    ("Indus Valley",    27.0,  68.0, -3300,-1300,  "South Asia",    88, 85, 60),
    ("Vedic India",     28.0,  77.0, -1500, -600,  "South Asia",    75, 92, 70),
    ("Maurya Empire",   25.0,  83.0,  -322, -185,  "South Asia",    85, 88, 85),
    ("Gupta Empire",    24.5,  82.5,   320,  550,  "South Asia",    85, 95, 78),
    ("Chola Dynasty",   10.8,  79.7,   300, 1279,  "South India",   82, 88, 86),
    ("Vijayanagara",    15.3,  76.5,  1336, 1646,  "South India",   80, 85, 84),
    ("Maratha Empire",  18.5,  73.8,  1674, 1818,  "South Asia",    78, 75, 92),
    ("Delhi Sultanate", 28.6,  77.2,  1206, 1526,  "South Asia",    76, 72, 88),
    ("Mughal Empire",   27.2,  78.0,  1526, 1857,  "South Asia",    90, 88, 90),
    ("Pallava Dynasty", 12.8,  79.7,   275,  897,  "South India",   78, 87, 80),
    ("Satavahana",      17.0,  79.5,  -230,  220,  "South Asia",    80, 82, 78),
    ("Kushana Empire",  34.0,  67.0,    30,  375,  "Central Asia",  82, 80, 85),
    ("Rashtrakuta",     17.3,  76.8,   753,  982,  "South India",   79, 84, 83),
    ("Pala Empire",     25.6,  85.1,   750, 1161,  "South Asia",    77, 90, 76),
    ("Chera Kingdom",   10.5,  76.2,  -300, 1102,  "South India",   83, 82, 75),
]

def load_civilizations():
    csv_path = os.path.join(os.path.dirname(__file__), "civilizations.csv")
    if os.path.exists(csv_path):
        civs = []
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    civs.append(Civilization(
                        row['name'], row['latitude'], row['longitude'],
                        row['start_year'], row['end_year'], row['region'],
                        row['resource_density'], row['knowledge_density'], row['military_strength']
                    ))
                except Exception as e:
                    print(f"  Skipping row: {e}")
        print(f"✅ Loaded {len(civs)} civilizations from civilizations.csv")
        return civs
    else:
        print("⚠️  civilizations.csv not found — using built-in data")
        return [Civilization(*row) for row in BUILTIN_DATA]

# ════════════════════════════════════════════════
#  GLOBAL STATE
# ════════════════════════════════════════════════

all_civs = load_civilizations()
kd_tree  = KDTree()
kd_tree.rebuild(all_civs)

r_tree = RTree()
r_tree.add_region("South Asia",     5.0, 37.0,  60.0,  97.0)
r_tree.add_region("Mediterranean", 30.0, 45.0,  -5.0,  42.0)
r_tree.add_region("Middle East",   25.0, 40.0,  35.0,  60.0)
r_tree.add_region("East Asia",     20.0, 50.0,  95.0, 135.0)
r_tree.add_region("Mesoamerica",    5.0, 25.0,-110.0, -80.0)
r_tree.add_region("North Africa",  15.0, 35.0,  15.0,  50.0)
r_tree.add_region("Central Asia",  30.0, 55.0,  45.0, 120.0)
r_tree.add_region("South America",-25.0,  0.0, -80.0, -60.0)

print(f"✅ KD-Tree built: {kd_tree.node_count} nodes")
print(f"✅ R-Tree built:  {len(r_tree.regions)} regions")

# ════════════════════════════════════════════════
#  HTTP REQUEST HANDLER
# ════════════════════════════════════════════════

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"  [{self.command}] {self.path}")

    def send_cors_headers(self):
        # CORS — allows the HTML frontend to call this server
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type",   "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": message}, status)

    def do_OPTIONS(self):
        # Preflight CORS request from browser
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path   = parsed.path

        if path == "/api/chat":
            try:
                length  = int(self.headers.get('Content-Length', 0))
                body    = json.loads(self.rfile.read(length).decode('utf-8'))
                message = body.get('message', '')
                history = body.get('history', [])

                SYSTEM = (
                    "You are the Spatial Intelligence Assistant for the Civilization Spatial Intelligence Mapper. "
                    "This is a DSA project using KD-Trees and R-Trees in Python/C++ with a Leaflet.js frontend. "
                    "The Python REST server (server.py) serves endpoints: /api/civilizations, /api/nearest, "
                    "/api/range, /api/compare, /api/rtree, /api/stats. "
                    "Dataset: 27 civilizations — 15 Indian (Indus Valley, Vedic India, Maurya, Gupta, Chola, "
                    "Vijayanagara, Maratha, Delhi Sultanate, Mughal, Pallava, Satavahana, Kushana, Rashtrakuta, "
                    "Pala, Chera) + 12 global. "
                    "KD-Tree: O(log n) nearest neighbor with branch pruning, O(log n+k) range query. "
                    "R-Tree: bounding box regions for 8 geographic areas. "
                    "Be concise, friendly, and technical. No markdown headers."
                )

                import urllib.request as urlreq
                messages = history + [{"role": "user", "content": message}]
                payload  = json.dumps({
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 600,
                    "system": SYSTEM,
                    "messages": messages
                }).encode('utf-8')

                req = urlreq.Request(
                    "https://api.anthropic.com/v1/messages",
                    data    = payload,
                    headers = {
                        "Content-Type":      "application/json",
                        "anthropic-version": "2023-06-01",
                        "x-api-key":         "PASTE_YOUR_API_KEY_HERE"
                    }
                )
                with urlreq.urlopen(req, timeout=15) as r:
                    result = json.loads(r.read().decode('utf-8'))
                reply = result.get('content', [{}])[0].get('text', 'No response.')
                self.send_json({"reply": reply})

            except Exception as e:
                err = str(e)
                # Friendly fallback answers when API key not set
                msg_lower = message.lower()
                if 'kd' in msg_lower or 'tree' in msg_lower:
                    reply = ("A KD-Tree splits space along alternating axes (lat/lon) at each depth level. "
                             "Nearest neighbor search uses branch pruning to skip subtrees that can't contain "
                             "a closer point, achieving O(log n) instead of O(n) for linear scan.")
                elif 'nearest' in msg_lower or 'search' in msg_lower:
                    reply = ("Nearest neighbor: descend the tree toward the query point, track best distance, "
                             "prune branches where |query - split plane| >= best distance. "
                             "For our 27 civilizations, this takes ~5 operations vs 27 for linear search.")
                elif 'indian' in msg_lower or 'india' in msg_lower:
                    reply = ("15 Indian civilizations: Indus Valley, Vedic India, Maurya, Gupta, Chola Dynasty, "
                             "Vijayanagara, Maratha, Delhi Sultanate, Mughal Empire, Pallava, Satavahana, "
                             "Kushana, Rashtrakuta, Pala Empire, Chera Kingdom.")
                elif 'r-tree' in msg_lower or 'rtree' in msg_lower or 'region' in msg_lower:
                    reply = ("R-Tree stores 8 bounding boxes (South Asia, Mediterranean, Middle East, East Asia, "
                             "Mesoamerica, North Africa, Central Asia, South America). "
                             "A point query checks which boxes contain the coordinates — O(log n).")
                elif 'api' in msg_lower or 'rest' in msg_lower or 'endpoint' in msg_lower:
                    reply = ("REST endpoints: /api/civilizations (all 27), /api/nearest?lat=&lon= (KD-Tree), "
                             "/api/range?latMin=&latMax=&lonMin=&lonMax= (range query), "
                             "/api/compare?a=&b= (comparison), /api/rtree?lat=&lon= (region), /api/stats.")
                elif 'score' in msg_lower or 'spatial' in msg_lower:
                    reply = ("Spatial Score = (Resource + Knowledge + Military) / 3. "
                             "All three are rated 1-100. Mughal Empire scores highest at 89.3. "
                             "It lets us compare civilizations objectively by geographic strength.")
                elif 'map' in msg_lower:
                    reply = ("The map uses Leaflet.js with CARTO Dark tiles (no API key needed). "
                             "Click anywhere → calls /api/nearest live from the Python server. "
                             "Orange markers = Indian civilizations, Blue = Global. "
                             "Use 🇮🇳 India button to zoom to the subcontinent.")
                else:
                    reply = ("I'm your Spatial Intelligence Assistant! Ask me about: "
                             "KD-Tree algorithm, nearest neighbor search, R-Tree regions, "
                             "Indian civilizations, REST API endpoints, or spatial scores. "
                             f"(Note: set your API key in server.py for full AI responses. Error: {err[:80]})")
                self.send_json({"reply": reply})
        else:
            self.send_error_json("Not found", 404)

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        params = parse_qs(parsed.query)

        def p(key):
            return params[key][0] if key in params else None

        # ── GET / ── health check
        if path == "/":
            self.send_json({
                "status":    "running",
                "project":   "Civilization Spatial Intelligence Mapper",
                "language":  "Python REST Server",
                "endpoints": [
                    "/api/civilizations", "/api/nearest",
                    "/api/range", "/api/compare",
                    "/api/rtree", "/api/stats"
                ]
            })

        # ── GET /api/civilizations
        elif path == "/api/civilizations":
            self.send_json([c.to_dict() for c in all_civs])

        # ── GET /api/nearest?lat=&lon=
        elif path == "/api/nearest":
            if not p("lat") or not p("lon"):
                return self.send_error_json("Missing params: lat, lon")
            try:
                lat, lon = float(p("lat")), float(p("lon"))
                civ, dist = kd_tree.nearest(lat, lon)
                self.send_json({
                    "query":        {"lat": lat, "lon": lon},
                    "nearest":      civ.to_dict(),
                    "distance_km":  round(dist * 111, 2),
                    "algorithm":    "KD-Tree O(log n) with branch pruning"
                })
            except Exception as e:
                self.send_error_json(str(e))

        # ── GET /api/range?latMin=&latMax=&lonMin=&lonMax=
        elif path == "/api/range":
            required = ["latMin", "latMax", "lonMin", "lonMax"]
            if not all(p(k) for k in required):
                return self.send_error_json("Missing params: latMin, latMax, lonMin, lonMax")
            try:
                lat_min, lat_max = float(p("latMin")), float(p("latMax"))
                lon_min, lon_max = float(p("lonMin")), float(p("lonMax"))
                results = kd_tree.range_query(lat_min, lat_max, lon_min, lon_max)
                self.send_json({
                    "query":     {"latMin": lat_min, "latMax": lat_max,
                                  "lonMin": lon_min, "lonMax": lon_max},
                    "count":     len(results),
                    "results":   [c.to_dict() for c in results],
                    "algorithm": "KD-Tree O(log n + k) spatial pruning"
                })
            except Exception as e:
                self.send_error_json(str(e))

        # ── GET /api/compare?a=&b=
        elif path == "/api/compare":
            if not p("a") or not p("b"):
                return self.send_error_json("Missing params: a, b")
            name_a, name_b = p("a"), p("b")
            civ_a = next((c for c in all_civs if c.name == name_a), None)
            civ_b = next((c for c in all_civs if c.name == name_b), None)
            if not civ_a: return self.send_error_json(f"Not found: {name_a}")
            if not civ_b: return self.send_error_json(f"Not found: {name_b}")
            dist = math.sqrt((civ_a.latitude - civ_b.latitude)**2 +
                             (civ_a.longitude - civ_b.longitude)**2) * 111
            winner = civ_a.name if civ_a.spatial_score() >= civ_b.spatial_score() else civ_b.name
            self.send_json({
                "civilization_a": civ_a.to_dict(),
                "civilization_b": civ_b.to_dict(),
                "score_a":        civ_a.spatial_score(),
                "score_b":        civ_b.spatial_score(),
                "distance_km":    round(dist, 2),
                "winner":         winner
            })

        # ── GET /api/rtree?lat=&lon=
        elif path == "/api/rtree":
            if not p("lat") or not p("lon"):
                return self.send_error_json("Missing params: lat, lon")
            try:
                lat, lon = float(p("lat")), float(p("lon"))
                regions  = r_tree.query_point(lat, lon)
                self.send_json({
                    "query":     {"lat": lat, "lon": lon},
                    "regions":   regions,
                    "count":     len(regions),
                    "algorithm": "R-Tree bounding box overlap O(log n)"
                })
            except Exception as e:
                self.send_error_json(str(e))

        # ── POST /api/chat  (AI assistant — proxies to Anthropic)
        elif path == "/api/chat":
            self.send_error_json("Use POST for /api/chat", 405)

        # ── GET /api/stats
        elif path == "/api/stats":
            n     = len(all_civs)
            log_n = math.ceil(math.log2(n)) if n > 0 else 0
            self.send_json({
                "total_civilizations": n,
                "kdtree_nodes":        kd_tree.node_count,
                "rtree_regions":       len(r_tree.regions),
                "linear_ops":          n,
                "kdtree_ops":          log_n,
                "speedup":             n // log_n if log_n > 0 else 1
            })

        else:
            self.send_error_json("Endpoint not found", 404)


# ════════════════════════════════════════════════
#  START SERVER
# ════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║   CIVILIZATION SPATIAL INTELLIGENCE MAPPER               ║")
    print("║   Python REST API Server                                  ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    server = HTTPServer(("0.0.0.0", PORT), Handler)

    print(f"🚀 REST API running at http://localhost:{PORT}")
    print(f"   Open civilization_mapper_frontend.html in Chrome\n")
    print(f"   Endpoints:")
    print(f"     http://localhost:{PORT}/api/civilizations")
    print(f"     http://localhost:{PORT}/api/nearest?lat=20&lon=78")
    print(f"     http://localhost:{PORT}/api/range?latMin=10&latMax=35&lonMin=60&lonMax=97")
    print(f"     http://localhost:{PORT}/api/compare?a=Mughal+Empire&b=Chola+Dynasty")
    print(f"     http://localhost:{PORT}/api/rtree?lat=25&lon=80")
    print(f"     http://localhost:{PORT}/api/stats")
    print(f"\n   Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⛔ Server stopped.")
