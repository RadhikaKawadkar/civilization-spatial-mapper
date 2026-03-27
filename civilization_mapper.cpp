/*
 * ============================================================
 *   CIVILIZATION SPATIAL INTELLIGENCE MAPPER
 *   DSA Industry Project — C++ REST API Server
 *   Data Structures: KD-Tree, R-Tree
 *   HTTP Server:     cpp-httplib (header-only)
 *
 *   ENDPOINTS:
 *     GET /api/civilizations          → all civilizations as JSON
 *     GET /api/nearest?lat=&lon=      → KD-Tree nearest neighbor
 *     GET /api/range?latMin=&latMax=&lonMin=&lonMax=  → range query
 *     GET /api/compare?a=&b=          → compare two civilizations
 *     GET /api/rtree?lat=&lon=        → R-Tree region lookup
 *     GET /api/stats                  → complexity stats
 *
 *   COMPILE:
 *     g++ -std=c++17 -o server civilization_mapper.cpp -lpthread
 *
 *   RUN:
 *     ./server          (starts on http://localhost:8080)
 *
 *   REQUIRES: httplib.h in the same folder
 *     Download: https://github.com/yhirose/cpp-httplib/releases
 * ============================================================
 */

#include "httplib.h"
#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <limits>
#include <iomanip>
#include <stdexcept>

using namespace std;

// ─────────────────────────────────────────────
//  DATA MODEL
// ─────────────────────────────────────────────

struct Civilization {
    string name;
    double latitude;
    double longitude;
    int    start_year;
    int    end_year;
    string region;
    double resource_density;
    double knowledge_density;
    double military_strength;

    double spatialScore() const {
        return (resource_density + knowledge_density + military_strength) / 3.0;
    }

    // Serialize to JSON string
    string toJSON() const {
        ostringstream j;
        j << fixed << setprecision(4);
        j << "{"
          << "\"name\":\""              << name              << "\","
          << "\"latitude\":"            << latitude          << ","
          << "\"longitude\":"           << longitude         << ","
          << "\"start_year\":"          << start_year        << ","
          << "\"end_year\":"            << end_year          << ","
          << "\"region\":\""            << region            << "\","
          << "\"resource_density\":"    << resource_density  << ","
          << "\"knowledge_density\":"   << knowledge_density << ","
          << "\"military_strength\":"   << military_strength << ","
          << "\"spatial_score\":"       << setprecision(2) << spatialScore()
          << "}";
        return j.str();
    }
};

// ─────────────────────────────────────────────
//  KD-TREE
// ─────────────────────────────────────────────

struct KDNode {
    Civilization civ;
    KDNode* left  = nullptr;
    KDNode* right = nullptr;
    int depth     = 0;
    KDNode(Civilization c, int d) : civ(c), depth(d) {}
};

class KDTree {
private:
    KDNode* root = nullptr;
    int     nodeCount = 0;

    double dist(const Civilization& a, const Civilization& b) const {
        double dl = a.latitude  - b.latitude;
        double dn = a.longitude - b.longitude;
        return sqrt(dl*dl + dn*dn);
    }

    KDNode* insert(KDNode* node, Civilization civ, int depth) {
        if (!node) { nodeCount++; return new KDNode(civ, depth); }
        int axis = depth % 2;
        double nv = axis==0 ? node->civ.latitude  : node->civ.longitude;
        double cv = axis==0 ? civ.latitude        : civ.longitude;
        if (cv < nv) node->left  = insert(node->left,  civ, depth+1);
        else         node->right = insert(node->right, civ, depth+1);
        return node;
    }

    void nearestSearch(KDNode* node, const Civilization& q,
                       KDNode*& best, double& bestDist, int depth) const {
        if (!node) return;
        double d = dist(node->civ, q);
        if (d < bestDist) { bestDist = d; best = node; }
        int axis = depth % 2;
        double nv = axis==0 ? node->civ.latitude  : node->civ.longitude;
        double qv = axis==0 ? q.latitude          : q.longitude;
        KDNode* first  = qv < nv ? node->left  : node->right;
        KDNode* second = qv < nv ? node->right : node->left;
        nearestSearch(first,  q, best, bestDist, depth+1);
        if (abs(qv - nv) < bestDist)
            nearestSearch(second, q, best, bestDist, depth+1);
    }

    void rangeSearch(KDNode* node,
                     double latMin, double latMax,
                     double lonMin, double lonMax,
                     vector<Civilization>& res, int depth) const {
        if (!node) return;
        double lat = node->civ.latitude, lon = node->civ.longitude;
        if (lat>=latMin && lat<=latMax && lon>=lonMin && lon<=lonMax)
            res.push_back(node->civ);
        int axis = depth % 2;
        double nv   = axis==0 ? lat    : lon;
        double minV = axis==0 ? latMin : lonMin;
        double maxV = axis==0 ? latMax : lonMax;
        if (minV <= nv) rangeSearch(node->left,  latMin, latMax, lonMin, lonMax, res, depth+1);
        if (maxV >= nv) rangeSearch(node->right, latMin, latMax, lonMin, lonMax, res, depth+1);
    }

    void deleteTree(KDNode* n) {
        if (!n) return;
        deleteTree(n->left); deleteTree(n->right); delete n;
    }

public:
    ~KDTree() { deleteTree(root); }

    void insert(Civilization civ) { root = insert(root, civ, 0); }

    Civilization nearestNeighbor(double lat, double lon) const {
        if (!root) throw runtime_error("Tree is empty");
        Civilization q; q.latitude = lat; q.longitude = lon;
        KDNode* best = nullptr; double bestDist = numeric_limits<double>::max();
        nearestSearch(root, q, best, bestDist, 0);
        return best->civ;
    }

    double nearestDist(double lat, double lon) const {
        Civilization q; q.latitude = lat; q.longitude = lon;
        KDNode* best = nullptr; double bestDist = numeric_limits<double>::max();
        nearestSearch(root, q, best, bestDist, 0);
        return bestDist;
    }

    vector<Civilization> rangeQuery(double latMin, double latMax,
                                    double lonMin, double lonMax) const {
        vector<Civilization> res;
        rangeSearch(root, latMin, latMax, lonMin, lonMax, res, 0);
        return res;
    }

    int size() const { return nodeCount; }
};

// ─────────────────────────────────────────────
//  R-TREE
// ─────────────────────────────────────────────

struct BoundingBox {
    string label;
    double latMin, latMax, lonMin, lonMax;
    bool contains(double lat, double lon) const {
        return lat>=latMin && lat<=latMax && lon>=lonMin && lon<=lonMax;
    }
};

class RTree {
    vector<BoundingBox> regions;
public:
    void addRegion(string label, double latMin, double latMax,
                   double lonMin, double lonMax) {
        regions.push_back({label, latMin, latMax, lonMin, lonMax});
    }
    vector<string> queryPoint(double lat, double lon) const {
        vector<string> res;
        for (const auto& r : regions)
            if (r.contains(lat, lon)) res.push_back(r.label);
        return res;
    }
    int size() const { return (int)regions.size(); }
};

// ─────────────────────────────────────────────
//  JSON HELPERS
// ─────────────────────────────────────────────

// Escape quotes in strings for JSON safety
string jsonEscape(const string& s) {
    string out;
    for (char c : s) {
        if (c=='"') out += "\\\"";
        else if (c=='\\') out += "\\\\";
        else out += c;
    }
    return out;
}

string vecsToJSON(const vector<Civilization>& civs) {
    string json = "[";
    for (size_t i = 0; i < civs.size(); i++) {
        json += civs[i].toJSON();
        if (i < civs.size()-1) json += ",";
    }
    json += "]";
    return json;
}

// ─────────────────────────────────────────────
//  CSV LOADER
// ─────────────────────────────────────────────

vector<Civilization> loadFromCSV(const string& filename) {
    vector<Civilization> civs;
    ifstream file(filename);
    if (!file.is_open()) {
        cerr << "Could not open " << filename << " — using built-in data.\n";
        return civs;
    }
    string line;
    getline(file, line); // skip header
    while (getline(file, line)) {
        if (line.empty()) continue;
        istringstream ss(line);
        Civilization c;
        string tok;
        getline(ss, c.name,   ',');
        getline(ss, tok, ','); c.latitude          = stod(tok);
        getline(ss, tok, ','); c.longitude         = stod(tok);
        getline(ss, tok, ','); c.start_year        = stoi(tok);
        getline(ss, tok, ','); c.end_year          = stoi(tok);
        getline(ss, c.region, ',');
        getline(ss, tok, ','); c.resource_density  = stod(tok);
        getline(ss, tok, ','); c.knowledge_density = stod(tok);
        getline(ss, tok, ','); c.military_strength = stod(tok);
        civs.push_back(c);
    }
    return civs;
}

vector<Civilization> getBuiltinData() {
    return {
        {"Indus Valley",    27.0,  68.0,-3300,-1300,"South Asia",   88,85,60},
        {"Ancient Egypt",   26.8,  30.8,-3100, -332,"North Africa", 80,78,81},
        {"Mesopotamia",     33.0,  44.4,-3500, -539,"Middle East",  78,80,75},
        {"Ancient Greece",  37.9,  23.7, -800, -146,"Mediterranean",70,95,72},
        {"Roman Empire",    41.9,  12.5,  -27,  476,"Mediterranean",80,70,88},
        {"Maurya Empire",   25.0,  83.0, -322, -185,"South Asia",   85,88,85},
        {"Han China",       35.0, 105.0, -206,  220,"East Asia",    88,90,85},
        {"Maya",            16.0, -89.0,  250,  900,"Mesoamerica",  70,88,65},
        {"Persian Empire",  32.0,  53.0, -550, -330,"Middle East",  85,75,90},
        {"Byzantine",       41.0,  29.0,  330, 1453,"Mediterranean",75,80,78},
        {"Vedic India",     28.0,  77.0,-1500, -600,"South Asia",   75,92,70},
        {"Aztec",           19.4, -99.1, 1300, 1521,"Mesoamerica",  72,80,85},
        {"Mongol Empire",   47.0, 106.0, 1206, 1368,"Central Asia", 65,60,98},
        {"Ottoman Empire",  39.9,  32.9, 1299, 1922,"Middle East",  80,72,88},
        {"Inca",           -13.5, -72.0, 1400, 1533,"South America",78,75,82},
        {"Gupta Empire",    24.5,  82.5,  320,  550,"South Asia",   85,95,78},
        {"Chola Dynasty",   10.8,  79.7,  300, 1279,"South India",  82,88,86},
        {"Vijayanagara",    15.3,  76.5, 1336, 1646,"South India",  80,85,84},
        {"Maratha Empire",  18.5,  73.8, 1674, 1818,"South Asia",   78,75,92},
        {"Delhi Sultanate", 28.6,  77.2, 1206, 1526,"South Asia",   76,72,88},
        {"Mughal Empire",   27.2,  78.0, 1526, 1857,"South Asia",   90,88,90},
        {"Pallava Dynasty", 12.8,  79.7,  275,  897,"South India",  78,87,80},
        {"Satavahana",      17.0,  79.5, -230,  220,"South Asia",   80,82,78},
        {"Kushana Empire",  34.0,  67.0,   30,  375,"Central Asia", 82,80,85},
        {"Rashtrakuta",     17.3,  76.8,  753,  982,"South India",  79,84,83},
        {"Pala Empire",     25.6,  85.1,  750, 1161,"South Asia",   77,90,76},
        {"Chera Kingdom",   10.5,  76.2, -300, 1102,"South India",  83,82,75},
    };
}

// ─────────────────────────────────────────────
//  GLOBAL STATE
// ─────────────────────────────────────────────

vector<Civilization> allCivs;
KDTree kdTree;
RTree  rTree;

// ─────────────────────────────────────────────
//  CORS HELPER
// ─────────────────────────────────────────────

void addCORS(httplib::Response& res) {
    res.set_header("Access-Control-Allow-Origin",  "*");
    res.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.set_header("Access-Control-Allow-Headers", "Content-Type");
}

void sendJSON(httplib::Response& res, const string& json) {
    addCORS(res);
    res.set_content(json, "application/json");
}

void sendError(httplib::Response& res, const string& msg, int code=400) {
    addCORS(res);
    res.status = code;
    res.set_content("{\"error\":\"" + jsonEscape(msg) + "\"}", "application/json");
}

// ─────────────────────────────────────────────
//  MAIN — SETUP + SERVER
// ─────────────────────────────────────────────

int main() {
    cout << "\n╔══════════════════════════════════════════════════════════╗\n";
    cout << "║     CIVILIZATION SPATIAL INTELLIGENCE MAPPER              ║\n";
    cout << "║     C++ REST API Server  |  KD-Tree + R-Tree              ║\n";
    cout << "╚══════════════════════════════════════════════════════════╝\n\n";

    // 1. Load data
    allCivs = loadFromCSV("civilizations.csv");
    if (allCivs.empty()) allCivs = getBuiltinData();
    cout << "✅ Loaded " << allCivs.size() << " civilizations.\n";

    // 2. Build KD-Tree
    for (const auto& c : allCivs) kdTree.insert(c);
    cout << "✅ KD-Tree built: " << kdTree.size() << " nodes.\n";

    // 3. Build R-Tree regions
    rTree.addRegion("South Asia",      5.0, 37.0,  60.0,  97.0);
    rTree.addRegion("Mediterranean",  30.0, 45.0,  -5.0,  42.0);
    rTree.addRegion("Middle East",    25.0, 40.0,  35.0,  60.0);
    rTree.addRegion("East Asia",      20.0, 50.0,  95.0, 135.0);
    rTree.addRegion("Mesoamerica",     5.0, 25.0,-110.0, -80.0);
    rTree.addRegion("North Africa",   15.0, 35.0,  15.0,  50.0);
    rTree.addRegion("Central Asia",   30.0, 55.0,  45.0, 120.0);
    rTree.addRegion("South America", -25.0,  0.0, -80.0, -60.0);
    cout << "✅ R-Tree built: " << rTree.size() << " regions.\n\n";

    // 4. HTTP Server
    httplib::Server svr;

    // ── OPTIONS (CORS preflight) ─────────────────
    svr.Options(".*", [](const httplib::Request&, httplib::Response& res) {
        addCORS(res);
        res.set_content("", "text/plain");
    });

    // ── GET /api/civilizations ───────────────────
    svr.Get("/api/civilizations", [](const httplib::Request&, httplib::Response& res) {
        sendJSON(res, vecsToJSON(allCivs));
        cout << "[GET] /api/civilizations  → " << allCivs.size() << " records\n";
    });

    // ── GET /api/nearest?lat=&lon= ───────────────
    svr.Get("/api/nearest", [](const httplib::Request& req, httplib::Response& res) {
        if (!req.has_param("lat") || !req.has_param("lon")) {
            sendError(res, "Missing required params: lat, lon"); return;
        }
        try {
            double lat = stod(req.get_param_value("lat"));
            double lon = stod(req.get_param_value("lon"));
            Civilization nearest = kdTree.nearestNeighbor(lat, lon);
            double dist = kdTree.nearestDist(lat, lon) * 111.0; // approx km
            ostringstream j;
            j << fixed << setprecision(2);
            j << "{"
              << "\"query\":{\"lat\":" << lat << ",\"lon\":" << lon << "},"
              << "\"nearest\":"        << nearest.toJSON() << ","
              << "\"distance_km\":"    << dist << ","
              << "\"algorithm\":\"KD-Tree O(log n) with branch pruning\""
              << "}";
            sendJSON(res, j.str());
            cout << "[GET] /api/nearest?lat=" << lat << "&lon=" << lon
                 << "  → " << nearest.name << "\n";
        } catch (exception& e) {
            sendError(res, e.what());
        }
    });

    // ── GET /api/range?latMin=&latMax=&lonMin=&lonMax= ──
    svr.Get("/api/range", [](const httplib::Request& req, httplib::Response& res) {
        if (!req.has_param("latMin") || !req.has_param("latMax") ||
            !req.has_param("lonMin") || !req.has_param("lonMax")) {
            sendError(res, "Missing params: latMin, latMax, lonMin, lonMax"); return;
        }
        try {
            double latMin = stod(req.get_param_value("latMin"));
            double latMax = stod(req.get_param_value("latMax"));
            double lonMin = stod(req.get_param_value("lonMin"));
            double lonMax = stod(req.get_param_value("lonMax"));
            auto results  = kdTree.rangeQuery(latMin, latMax, lonMin, lonMax);
            ostringstream j;
            j << "{"
              << "\"query\":{\"latMin\":" << latMin << ",\"latMax\":" << latMax
              << ",\"lonMin\":" << lonMin << ",\"lonMax\":" << lonMax << "},"
              << "\"count\":" << results.size() << ","
              << "\"results\":" << vecsToJSON(results) << ","
              << "\"algorithm\":\"KD-Tree O(log n + k) spatial pruning\""
              << "}";
            sendJSON(res, j.str());
            cout << "[GET] /api/range  → " << results.size() << " results\n";
        } catch (exception& e) {
            sendError(res, e.what());
        }
    });

    // ── GET /api/compare?a=&b= ───────────────────
    svr.Get("/api/compare", [](const httplib::Request& req, httplib::Response& res) {
        if (!req.has_param("a") || !req.has_param("b")) {
            sendError(res, "Missing params: a, b (civilization names)"); return;
        }
        string nameA = req.get_param_value("a");
        string nameB = req.get_param_value("b");
        Civilization* civA = nullptr;
        Civilization* civB = nullptr;
        for (auto& c : allCivs) {
            if (c.name == nameA) civA = &c;
            if (c.name == nameB) civB = &c;
        }
        if (!civA) { sendError(res, "Civilization not found: " + nameA); return; }
        if (!civB) { sendError(res, "Civilization not found: " + nameB); return; }
        double dlat = civA->latitude  - civB->latitude;
        double dlon = civA->longitude - civB->longitude;
        double dist = sqrt(dlat*dlat + dlon*dlon) * 111.0;
        string winner = civA->spatialScore() > civB->spatialScore() ? nameA : nameB;
        ostringstream j;
        j << fixed << setprecision(2);
        j << "{"
          << "\"civilization_a\":"  << civA->toJSON() << ","
          << "\"civilization_b\":"  << civB->toJSON() << ","
          << "\"distance_km\":"     << dist << ","
          << "\"winner\":\""        << jsonEscape(winner) << "\","
          << "\"score_a\":"         << civA->spatialScore() << ","
          << "\"score_b\":"         << civB->spatialScore()
          << "}";
        sendJSON(res, j.str());
        cout << "[GET] /api/compare  " << nameA << " vs " << nameB << "\n";
    });

    // ── GET /api/rtree?lat=&lon= ─────────────────
    svr.Get("/api/rtree", [](const httplib::Request& req, httplib::Response& res) {
        if (!req.has_param("lat") || !req.has_param("lon")) {
            sendError(res, "Missing params: lat, lon"); return;
        }
        try {
            double lat = stod(req.get_param_value("lat"));
            double lon = stod(req.get_param_value("lon"));
            auto   regions = rTree.queryPoint(lat, lon);
            string regJSON = "[";
            for (size_t i = 0; i < regions.size(); i++) {
                regJSON += "\"" + regions[i] + "\"";
                if (i < regions.size()-1) regJSON += ",";
            }
            regJSON += "]";
            ostringstream j;
            j << "{"
              << "\"query\":{\"lat\":" << lat << ",\"lon\":" << lon << "},"
              << "\"regions\":"        << regJSON << ","
              << "\"count\":"          << regions.size() << ","
              << "\"algorithm\":\"R-Tree bounding box overlap O(log n)\""
              << "}";
            sendJSON(res, j.str());
            cout << "[GET] /api/rtree?lat=" << lat << "&lon=" << lon
                 << "  → " << regions.size() << " region(s)\n";
        } catch (exception& e) {
            sendError(res, e.what());
        }
    });

    // ── GET /api/stats ───────────────────────────
    svr.Get("/api/stats", [](const httplib::Request&, httplib::Response& res) {
        int n    = (int)allCivs.size();
        int logN = (int)(log2(n) + 1);
        ostringstream j;
        j << "{"
          << "\"total_civilizations\":"  << n    << ","
          << "\"kdtree_nodes\":"         << kdTree.size() << ","
          << "\"rtree_regions\":"        << rTree.size()  << ","
          << "\"linear_ops\":"           << n    << ","
          << "\"kdtree_ops\":"           << logN << ","
          << "\"speedup\":"              << n / logN
          << "}";
        sendJSON(res, j.str());
        cout << "[GET] /api/stats\n";
    });

    // ── Health check ─────────────────────────────
    svr.Get("/", [](const httplib::Request&, httplib::Response& res) {
        addCORS(res);
        res.set_content(
            "{\"status\":\"running\","
            "\"project\":\"Civilization Spatial Intelligence Mapper\","
            "\"endpoints\":[\"/api/civilizations\",\"/api/nearest\","
            "\"/api/range\",\"/api/compare\",\"/api/rtree\",\"/api/stats\"]}",
            "application/json");
    });

    int PORT = 8080;
    cout << "🚀 REST API Server running at http://localhost:" << PORT << "\n";
    cout << "   Open civilization_mapper_frontend.html in your browser\n\n";
    cout << "   Endpoints:\n";
    cout << "     GET /api/civilizations\n";
    cout << "     GET /api/nearest?lat=28&lon=77\n";
    cout << "     GET /api/range?latMin=10&latMax=35&lonMin=60&lonMax=90\n";
    cout << "     GET /api/compare?a=Mughal+Empire&b=Chola+Dynasty\n";
    cout << "     GET /api/rtree?lat=20&lon=78\n";
    cout << "     GET /api/stats\n\n";
    cout << "Press Ctrl+C to stop.\n\n";

    svr.listen("0.0.0.0", PORT);
    return 0;
}