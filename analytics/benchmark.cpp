#include "benchmark.h"
#include <chrono>
#include <iostream>
#include <limits>

double linearSearch(
    const std::vector<Civilization>& civs,
    double lat,
    double lon)
{
    double best = std::numeric_limits<double>::max();

    for(const auto& c : civs)
    {
        double d = distance(lat, lon, c.latitude, c.longitude);
        if(d < best)
            best = d;
    }

    return best;
}

void benchmarkKDTree(KDNode* root,
                     const std::vector<Civilization>& civs)
{
    double qlat = 30;
    double qlon = 70;

    Civilization nearest;
    double bestDist = std::numeric_limits<double>::max();

    auto startKD = std::chrono::high_resolution_clock::now();

    nearestNeighbor(root, qlat, qlon, nearest, bestDist, 0);

    auto endKD = std::chrono::high_resolution_clock::now();

    auto kdTime =
        std::chrono::duration_cast<std::chrono::microseconds>(
            endKD - startKD);

    auto startLinear = std::chrono::high_resolution_clock::now();

    linearSearch(civs, qlat, qlon);

    auto endLinear = std::chrono::high_resolution_clock::now();

    auto linearTime =
        std::chrono::duration_cast<std::chrono::microseconds>(
            endLinear - startLinear);

    std::cout << "\nBenchmark Results:\n";
    std::cout << "KD Tree Time: "
              << kdTime.count() << " microseconds\n";

    std::cout << "Linear Search Time: "
              << linearTime.count() << " microseconds\n";
}
