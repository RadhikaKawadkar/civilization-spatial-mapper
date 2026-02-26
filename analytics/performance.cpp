#include <iostream>
#include <chrono>
#include "../core/kd_tree.h"
#include "../core/r_tree.h"

void benchmarkKDTree(KDNode* root) {
    auto start = std::chrono::high_resolution_clock::now();

    std::vector<Civilization> result;
    rangeSearch(root, 20, 30, 70, 85, 0, result);

    auto end = std::chrono::high_resolution_clock::now();
    std::cout << "KD-Tree range query time: "
              << std::chrono::duration<double, std::milli>(end - start).count()
              << " ms\n";
}

void benchmarkRTree(RTree& tree) {
    auto start = std::chrono::high_resolution_clock::now();

    tree.rangeQuery(20, 30, 70, 85);

    auto end = std::chrono::high_resolution_clock::now();
    std::cout << "R-Tree range query time: "
              << std::chrono::duration<double, std::milli>(end - start).count()
              << " ms\n";
}