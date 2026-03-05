#include <iostream>
#include <vector>
#include "core/rtree/rtree.h"
#include "core/kd_tree.h"
#include <chrono>
#include <random>

int main() {
    auto startKD = std::chrono::high_resolution_clock::now();
    KDNode* root = nullptr;
    std::mt19937 gen(42);
    std::uniform_real_distribution<double> lat_dis(-90.0, 90.0);
    std::uniform_real_distribution<double> lon_dis(-180.0, 180.0);
    
    std::vector<Point> pts;
    for(int i=0; i<10000; i++) {
        Civilization c{i, "Test", lat_dis(gen), lon_dis(gen), 2000};
        root = insertKD(root, c, 0);
        pts.push_back({c.longitude, c.latitude, c});
    }

    auto endKD = std::chrono::high_resolution_clock::now();
    
    auto startRTree = std::chrono::high_resolution_clock::now();
    RTree rtree(4);
    for(auto& p : pts) {
        rtree.insert(p);
    }
    auto endRTree = std::chrono::high_resolution_clock::now();
    
    std::cout << "[10,000 Nodes Test]\n";
    std::cout << "KD-Tree Insert Time: " << std::chrono::duration_cast<std::chrono::milliseconds>(endKD - startKD).count() << " ms\n";
    std::cout << "R-Tree Insert Time: " << std::chrono::duration_cast<std::chrono::milliseconds>(endRTree - startRTree).count() << " ms\n";
    
    // Search
    auto s1 = std::chrono::high_resolution_clock::now();
    Civilization kdNearest; double bdKD = 1000000;
    nearestNeighbor(root, 30.0, 70.0, kdNearest, bdKD, 0);
    auto e1 = std::chrono::high_resolution_clock::now();
    
    auto s2 = std::chrono::high_resolution_clock::now();
    Civilization rtNearest; double bdRT = 1000000;
    Point q = {70.0, 30.0, Civilization()};
    rtree.nearestNeighbor(q, rtNearest, bdRT);
    auto e2 = std::chrono::high_resolution_clock::now();
    
    std::cout << "\nKD-Tree NN Search Time: " << std::chrono::duration_cast<std::chrono::microseconds>(e1 - s1).count() << " us (Dist: " << bdKD << ")\n";
    std::cout << "R-Tree NN Search Time: " << std::chrono::duration_cast<std::chrono::microseconds>(e2 - s2).count() << " us (Dist: " << bdRT << ")\n";
    
    return 0;
}
