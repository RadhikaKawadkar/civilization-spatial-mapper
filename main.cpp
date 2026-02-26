#include <iostream>
#include "core/kd_tree.h"
#include "core/r_tree.h"
#include "data/csv_loader.h"

void benchmarkKDTree(KDNode*);
void benchmarkRTree(RTree&);

int main() {
    auto civs = loadCivilizations("data/final_dataset.csv");
    std::cout << "Loaded: " << civs.size() << " civilizations\n";

    KDNode* root = nullptr;
    for (auto& c : civs)
        root = insertKD(root, c, 0);

    RTree rtree;
    for (auto& c : civs) {
        rtree.insert({c.latitude, c.latitude, c.longitude, c.longitude, c.name});
    }

    benchmarkKDTree(root);
    benchmarkRTree(rtree);

    Civilization nearest;
    double best = 1e9;
    nearestNeighbor(root, 28.6, 77.2, nearest, best, 0);

    std::cout << "Nearest civilization: " << nearest.name << "\n";
    return 0;
}