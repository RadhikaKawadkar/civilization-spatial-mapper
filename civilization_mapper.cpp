/*
 * ============================================================
 *   CIVILIZATION SPATIAL INTELLIGENCE MAPPER
 *   DSA Industry Project — C++ Implementation
 *   Data Structures: KD-Tree, R-Tree (concept), Multi-dim Index
 * ============================================================
 */

#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <limits>
#include <iomanip>
#include <queue>

using namespace std;

// ---------------------------------------------
//  DATA MODEL
// ---------------------------------------------

struct Civilization {
    string name;
    double latitude;
    double longitude;
    int start_year;   // BCE = negative
    int end_year;
    string region;
    double resource_density;
    double knowledge_density;
    double military_strength;

    // Computed spatial score
    double spatialScore() const {
        return (resource_density + knowledge_density + military_strength) / 3.0;
    }
};

// ---------------------------------------------
//  KD-TREE NODE
// ---------------------------------------------

struct KDNode {
    Civilization civ;
    KDNode* left;
    KDNode* right;
    int depth;

    KDNode(Civilization c, int d) : civ(c), left(nullptr), right(nullptr), depth(d) {}
};

// ---------------------------------------------
//  KD-TREE CLASS
// ---------------------------------------------

class KDTree {
private:
    KDNode* root;
    int size;

    // Euclidean distance between two civilizations (lat/lon space)
    double distance(const Civilization& a, const Civilization& b) const {
        double dlat = a.latitude - b.latitude;
        double dlon = a.longitude - b.longitude;
        return sqrt(dlat * dlat + dlon * dlon);
    }

    // Insert recursively
    KDNode* insert(KDNode* node, Civilization civ, int depth) {
        if (!node) {
            size++;
            return new KDNode(civ, depth);
        }
        int axis = depth % 2; // 0 = latitude, 1 = longitude
        double nodeVal = (axis == 0) ? node->civ.latitude : node->civ.longitude;
        double civVal  = (axis == 0) ? civ.latitude : civ.longitude;

        if (civVal < nodeVal)
            node->left = insert(node->left, civ, depth + 1);
        else
            node->right = insert(node->right, civ, depth + 1);

        return node;
    }

    // Nearest neighbor search
    void nearestSearch(KDNode* node, const Civilization& query,
                       KDNode*& best, double& bestDist, int depth) const {
        if (!node) return;

        double d = distance(node->civ, query);
        if (d < bestDist) {
            bestDist = d;
            best = node;
        }

        int axis = depth % 2;
        double nodeVal  = (axis == 0) ? node->civ.latitude  : node->civ.longitude;
        double queryVal = (axis == 0) ? query.latitude       : query.longitude;

        KDNode* first  = (queryVal < nodeVal) ? node->left  : node->right;
        KDNode* second = (queryVal < nodeVal) ? node->right : node->left;

        nearestSearch(first, query, best, bestDist, depth + 1);

        // Pruning: only explore other branch if it could have closer point
        if (abs(queryVal - nodeVal) < bestDist)
            nearestSearch(second, query, best, bestDist, depth + 1);
    }

    // Range query (bounding box)
    void rangeSearch(KDNode* node,
                     double latMin, double latMax,
                     double lonMin, double lonMax,
                     vector<Civilization>& result, int depth) const {
        if (!node) return;

        double lat = node->civ.latitude;
        double lon = node->civ.longitude;

        if (lat >= latMin && lat <= latMax && lon >= lonMin && lon <= lonMax)
            result.push_back(node->civ);

        int axis = depth % 2;
        double nodeVal = (axis == 0) ? lat : lon;
        double minVal  = (axis == 0) ? latMin : lonMin;
        double maxVal  = (axis == 0) ? latMax : lonMax;

        if (minVal <= nodeVal) rangeSearch(node->left,  latMin, latMax, lonMin, lonMax, result, depth + 1);
        if (maxVal >= nodeVal) rangeSearch(node->right, latMin, latMax, lonMin, lonMax, result, depth + 1);
    }

    // Inorder traversal for display
    void inorder(KDNode* node, int indent = 0) const {
        if (!node) return;
        inorder(node->left, indent + 2);
        cout << string(indent, ' ') << "["
             << node->civ.name << " | "
             << fixed << setprecision(2)
             << node->civ.latitude << ", " << node->civ.longitude
             << " | Score: " << node->civ.spatialScore() << "]\n";
        inorder(node->right, indent + 2);
    }

    void deleteTree(KDNode* node) {
        if (!node) return;
        deleteTree(node->left);
        deleteTree(node->right);
        delete node;
    }

public:
    KDTree() : root(nullptr), size(0) {}
    ~KDTree() { deleteTree(root); }

    void insert(Civilization civ) {
        root = insert(root, civ, 0);
    }

    Civilization nearestNeighbor(double lat, double lon) const {
        if (!root) throw runtime_error("Tree is empty");
        Civilization query;
        query.latitude = lat;
        query.longitude = lon;
        KDNode* best = nullptr;
        double bestDist = numeric_limits<double>::max();
        nearestSearch(root, query, best, bestDist, 0);
        return best->civ;
    }

    vector<Civilization> rangeQuery(double latMin, double latMax,
                                    double lonMin, double lonMax) const {
        vector<Civilization> result;
        rangeSearch(root, latMin, latMax, lonMin, lonMax, result, 0);
        return result;
    }

    void printTree() const {
        cout << "\n📊 KD-Tree (Inorder Traversal):\n";
        cout << string(60, '=') << "\n";
        inorder(root);
    }

    int getSize() const { return size; }
};

// ---------------------------------------------
//  R-TREE (Bounding Box Concept Implementation)
// ---------------------------------------------

struct BoundingBox {
    double latMin, latMax, lonMin, lonMax;
    string label;

    bool overlaps(double lat, double lon) const {
        return lat >= latMin && lat <= latMax && lon >= lonMin && lon <= lonMax;
    }
};

class RTree {
private:
    vector<BoundingBox> regions;

public:
    void addRegion(string label, double latMin, double latMax,
                   double lonMin, double lonMax) {
        regions.push_back({latMin, latMax, lonMin, lonMax, label});
    }

    vector<string> queryPoint(double lat, double lon) const {
        vector<string> result;
        for (const auto& r : regions)
            if (r.overlaps(lat, lon))
                result.push_back(r.label);
        return result;
    }

    void printRegions() const {
        cout << "\n🗺️  R-Tree Bounding Boxes (Regional Index):\n";
        cout << string(60, '=') << "\n";
        for (const auto& r : regions) {
            cout << "  Region: " << setw(20) << left << r.label
                 << " | Lat[" << r.latMin << " - " << r.latMax << "]"
                 << " Lon[" << r.lonMin << " - " << r.lonMax << "]\n";
        }
    }
};

// ---------------------------------------------
//  CSV LOADER
// ---------------------------------------------

vector<Civilization> loadFromCSV(const string& filename) {
    vector<Civilization> civs;
    ifstream file(filename);
    if (!file.is_open()) {
        cerr << "⚠️  Could not open " << filename << ". Using built-in dataset.\n";
        return civs;
    }
    string line;
    getline(file, line); // skip header
    while (getline(file, line)) {
        istringstream ss(line);
        Civilization c;
        string tok;
        getline(ss, c.name, ',');
        getline(ss, tok, ','); c.latitude = stod(tok);
        getline(ss, tok, ','); c.longitude = stod(tok);
        getline(ss, tok, ','); c.start_year = stoi(tok);
        getline(ss, tok, ','); c.end_year = stoi(tok);
        getline(ss, c.region, ',');
        getline(ss, tok, ','); c.resource_density = stod(tok);
        getline(ss, tok, ','); c.knowledge_density = stod(tok);
        getline(ss, tok, ','); c.military_strength = stod(tok);
        civs.push_back(c);
    }
    return civs;
}

// ---------------------------------------------
//  BUILT-IN DATASET (fallback)
// ---------------------------------------------

vector<Civilization> getBuiltinData() {
    return {
        {"Indus Valley",    23.5,  68.4, -3300, -1300, "South Asia",    85, 82, 60},
        {"Ancient Egypt",   26.8,  30.8, -3100,  -332, "North Africa",  80, 78, 81},
        {"Mesopotamia",     33.0,  44.4, -3500,  -539, "Middle East",   78, 80, 75},
        {"Ancient Greece",  37.9,  23.7, -800,   -146, "Mediterranean", 70, 95, 72},
        {"Roman Empire",    41.9,  12.5,  -27,    476, "Mediterranean", 80, 70, 88},
        {"Maurya Empire",   25.0,  83.0, -322,   -185, "South Asia",    82, 85, 80},
        {"Han China",       35.0, 105.0, -206,    220, "East Asia",     88, 90, 85},
        {"Maya",            16.0,  -89.0, 250,   900,  "Mesoamerica",   70, 88, 65},
        {"Persian Empire",  32.0,  53.0, -550,   -330, "Middle East",   85, 75, 90},
        {"Byzantine",       41.0,  29.0,  330,   1453, "Mediterranean", 75, 80, 78},
        {"Vedic India",     28.0,  77.0, -1500,  -600, "South Asia",    75, 90, 70},
        {"Aztec",           19.4,  -99.1, 1300,  1521, "Mesoamerica",   72, 80, 85},
        {"Mongol Empire",   47.0,  106.0, 1206,  1368, "Central Asia",  65, 60, 98},
        {"Ottoman Empire",  39.9,  32.9,  1299,  1922, "Middle East",   80, 72, 88},
        {"Inca",           -13.5,  -72.0, 1400,  1533, "South America", 78, 75, 82},
    };
}

// ---------------------------------------------
//  ANALYSIS & COMPARISON ENGINE
// ---------------------------------------------

void compareCivilizations(const Civilization& a, const Civilization& b) {
    double dlat = abs(a.latitude - b.latitude);
    double dlon = abs(a.longitude - b.longitude);
    double dist = sqrt(dlat*dlat + dlon*dlon) * 111.0; // approx km

    cout << "\n🔍 Comparative Geographic Analysis\n";
    cout << string(60, '=') << "\n";
    cout << left << setw(25) << "Attribute"
         << setw(20) << a.name << setw(20) << b.name << "\n";
    cout << string(65, '=') << "\n";
    cout << setw(25) << "Latitude"
         << setw(20) << a.latitude << setw(20) << b.latitude << "\n";
    cout << setw(25) << "Longitude"
         << setw(20) << a.longitude << setw(20) << b.longitude << "\n";
    cout << setw(25) << "Resource Density"
         << setw(20) << a.resource_density << setw(20) << b.resource_density << "\n";
    cout << setw(25) << "Knowledge Density"
         << setw(20) << a.knowledge_density << setw(20) << b.knowledge_density << "\n";
    cout << setw(25) << "Military Strength"
         << setw(20) << a.military_strength << setw(20) << b.military_strength << "\n";
    cout << setw(25) << "Spatial Score"
         << setw(20) << fixed << setprecision(2) << a.spatialScore()
         << setw(20) << b.spatialScore() << "\n";
    cout << string(65, '=') << "\n";
    cout << "📏 Geographic Distance: ~" << fixed << setprecision(1)
         << dist << " km\n";

    string winner = (a.spatialScore() > b.spatialScore()) ? a.name : b.name;
    cout << "🏆 Higher Spatial Score: " << winner << "\n";
}

void complexityAnalysis(int n) {
    cout << "\n⏱️  Time Complexity Analysis (n = " << n << " civilizations)\n";
    cout << string(60, '=') << "\n";
    cout << left << setw(30) << "Method"
         << setw(15) << "Complexity"
         << setw(15) << "Operations\n";
    cout << string(60, '=') << "\n";
    cout << setw(30) << "Linear Search"
         << setw(15) << "O(n)"
         << setw(15) << n << "\n";
    int kdOps = (int)(log2(n) + 1);
    cout << setw(30) << "KD-Tree (avg)"
         << setw(15) << "O(log n)"
         << setw(15) << kdOps << "\n";
    int rtreeOps = (int)(log2(n) * 2);
    cout << setw(30) << "R-Tree Range"
         << setw(15) << "O(log n + k)"
         << setw(15) << rtreeOps << "\n";
    cout << string(60, '=') << "\n";
    cout << "🚀 KD-Tree is ~" << (n / kdOps) << "x faster than linear search!\n";
}

// ---------------------------------------------
//  MAIN PROGRAM
// ---------------------------------------------

int main() {
    cout << "\n";
    cout << "╔══════════════════════════════════════════════════════════╗\n";
    cout << "║     🗺️  CIVILIZATION SPATIAL INTELLIGENCE MAPPER          ║\n";
    cout << "║     DSA Industry Project | KD-Trees + R-Trees            ║\n";
    cout << "╚══════════════════════════════════════════════════════════╝\n\n";

    // -- 1. Data Ingestion --
    vector<Civilization> civs = loadFromCSV("civilizations.csv");
    if (civs.empty()) civs = getBuiltinData();

    cout << "✅ Data Ingestion Complete: " << civs.size() << " civilizations loaded.\n";

    // -- 2. Build KD-Tree --
    KDTree kdTree;
    for (const auto& c : civs) kdTree.insert(c);
    cout << "✅ KD-Tree Built: " << kdTree.getSize() << " nodes indexed.\n";

    // -- 3. Build R-Tree Regions --
    RTree rTree;
    rTree.addRegion("South Asia",      10.0, 35.0, 60.0, 90.0);
    rTree.addRegion("Mediterranean",   30.0, 45.0, -5.0, 42.0);
    rTree.addRegion("Middle East",     25.0, 40.0, 35.0, 60.0);
    rTree.addRegion("East Asia",       20.0, 50.0, 95.0, 135.0);
    rTree.addRegion("Mesoamerica",      5.0, 25.0,-110.0,-80.0);
    rTree.addRegion("North Africa",    15.0, 35.0, 15.0, 50.0);
    rTree.addRegion("Central Asia",    40.0, 55.0, 60.0, 120.0);
    rTree.addRegion("South America",  -25.0,  0.0,-80.0, -60.0);
    cout << "✅ R-Tree Regions Indexed.\n";

    // -- 4. Print Tree --
    kdTree.printTree();
    rTree.printRegions();

    // -- 5. Query: Nearest Neighbor --
    cout << "\n🔎 Query 1: Nearest Civilization to (30.0, 70.0)\n";
    cout << string(60, '=') << "\n";
    Civilization nearest = kdTree.nearestNeighbor(30.0, 70.0);
    cout << "  → Nearest: " << nearest.name
         << " [" << nearest.latitude << ", " << nearest.longitude << "]\n"
         << "  → Region : " << nearest.region
         << " | Spatial Score: " << fixed << setprecision(2) << nearest.spatialScore() << "\n";

    // -- 6. Query: Range --
    cout << "\n🔎 Query 2: Range Query — Lat[20–40], Lon[25–90]\n";
    cout << string(60, '=') << "\n";
    auto rangeResult = kdTree.rangeQuery(20.0, 40.0, 25.0, 90.0);
    cout << "  Found " << rangeResult.size() << " civilization(s):\n";
    for (const auto& c : rangeResult)
        cout << "    • " << left << setw(22) << c.name
             << " | Score: " << c.spatialScore() << "\n";

    // -- 7. R-Tree Point Query --
    cout << "\n🔎 Query 3: R-Tree Point Query — (25.0, 75.0)\n";
    cout << string(60, '=') << "\n";
    auto regions = rTree.queryPoint(25.0, 75.0);
    cout << "  Matching regions: ";
    for (const auto& r : regions) cout << r << "  ";
    cout << "\n";

    // -- 8. Comparative Analysis --
    compareCivilizations(civs[0], civs[1]); // Indus vs Egypt

    // -- 9. Complexity Analysis --
    complexityAnalysis(civs.size());

    // -- 10. Export JSON for Frontend --
    ofstream json("civilizations_data.json");
    json << "[\n";
    for (size_t i = 0; i < civs.size(); ++i) {
        const auto& c = civs[i];
        json << "  {\n"
             << "    \"name\": \"" << c.name << "\",\n"
             << "    \"latitude\": " << c.latitude << ",\n"
             << "    \"longitude\": " << c.longitude << ",\n"
             << "    \"start_year\": " << c.start_year << ",\n"
             << "    \"end_year\": " << c.end_year << ",\n"
             << "    \"region\": \"" << c.region << "\",\n"
             << "    \"resource_density\": " << c.resource_density << ",\n"
             << "    \"knowledge_density\": " << c.knowledge_density << ",\n"
             << "    \"military_strength\": " << c.military_strength << ",\n"
             << "    \"spatial_score\": " << fixed << setprecision(2) << c.spatialScore() << "\n"
             << "  }" << (i < civs.size()-1 ? "," : "") << "\n";
    }
    json << "]\n";
    json.close();

    cout << "\n✅ JSON exported → civilizations_data.json (for frontend)\n";
    cout << "\n╔══════════════════════════════════════════════════════════╗\n";
    cout << "║  ✔ All queries complete. System ready for viva demo.      ║\n";
    cout << "╚══════════════════════════════════════════════════════════╝\n\n";

    return 0;
}
