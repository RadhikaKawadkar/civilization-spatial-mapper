#include "benchmark.h"
#include <iostream>
#include <vector>
#include <chrono>
#include <random>
#include <iomanip>

void runSpatialScalingTest() {
    std::vector<int> sizes = {10000, 50000, 100000, 250000, 500000};
    
    std::mt19937 gen(42);
    std::uniform_real_distribution<double> lat_dis(-90.0, 90.0);
    std::uniform_real_distribution<double> lon_dis(-180.0, 180.0);
    
    std::cout << "\n======================================================\n";
    std::cout << "          R-Tree Spatial Scaling Benchmark          \n";
    std::cout << "======================================================\n";
    std::cout << std::left << std::setw(15) << "Dataset Size" 
              << std::setw(20) << "Insert Time (ms)" 
              << std::setw(20) << "Range Query (ms)" 
              << std::setw(20) << "NN Search (us)" << "\n";
    std::cout << "------------------------------------------------------\n";

    for (int size : sizes) {
        RTree rtree(8); // MAX_CHILDREN 8 is generally better for large sets
        
        std::vector<Point> testPoints;
        for (int i = 0; i < size; ++i) {
            Civilization c{i, "Benchmark", lat_dis(gen), lon_dis(gen), 2000};
            Point p = {c.longitude, c.latitude, c};
            testPoints.push_back(p);
        }
        
        auto startInsert = std::chrono::high_resolution_clock::now();
        for (const auto& p : testPoints) {
            rtree.insert(p);
        }
        auto endInsert = std::chrono::high_resolution_clock::now();
        double insertMs = std::chrono::duration_cast<std::chrono::milliseconds>(endInsert - startInsert).count();
        
        // Range Query Test: query roughly a 10x10 degree box from the center
        Rectangle queryBox(-5.0, -5.0, 5.0, 5.0);
        auto startRange = std::chrono::high_resolution_clock::now();
        auto results = rtree.search(queryBox);
        auto endRange = std::chrono::high_resolution_clock::now();
        double rangeMs = std::chrono::duration_cast<std::chrono::milliseconds>(endRange - startRange).count();
        
        // Nearest Neighbor Test
        Point queryPt = {45.0, 45.0, Civilization()};
        Civilization best;
        double bestDist;
        auto startNN = std::chrono::high_resolution_clock::now();
        rtree.nearestNeighbor(queryPt, best, bestDist);
        auto endNN = std::chrono::high_resolution_clock::now();
        double nnUs = std::chrono::duration_cast<std::chrono::microseconds>(endNN - startNN).count();
        
        std::cout << std::left << std::setw(15) << size 
                  << std::setw(20) << insertMs 
                  << std::setw(20) << rangeMs 
                  << std::setw(20) << nnUs << "\n";
    }
    std::cout << "======================================================\n";
}
