#include "utils/logger.h"
#include "analytics/benchmark.h"
#include <iostream>
#include <iomanip>
#include <limits>

void displayMenu()
{
    std::cout << "\n======================================================\n";
    std::cout << "      Civilization Spatial Intelligence System      \n";
    std::cout << "======================================================\n";
    std::cout << "  1. Nearest Civilization Search\n";
    std::cout << "  2. Range Query Search\n";
    std::cout << "  3. KD-Tree Structure View\n";
    std::cout << "  4. Performance Benchmark Results\n";
    std::cout << "  5. Exit System\n";
    std::cout << "======================================================\n";
    std::cout << "Select Operation Mode (1-5): ";
}

int main()
{
    Logger::info("Initializing Spatial Intelligence System...");
    Logger::info("Loading dataset components...");

    auto civs = loadCivilizations("data/final_dataset.csv");

    Logger::info("Constructing KD-Tree Engine...");
    KDNode* root = nullptr;

    for (const auto& c : civs)
        root = insertKD(root, c, 0);

    Logger::info("System Architecture successfully deployed.");

    int choice;

    while (true)
    {
        displayMenu();

        if (!(std::cin >> choice))
        {
            std::cin.clear();
            std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
            Logger::warn("Invalid input. Please enter a numerical value.");
            continue;
        }

        if (choice == 1)
        {
            std::cout << "\n------------------------------------------------------\n";
            std::cout << "            Nearest Civilization Search             \n";
            std::cout << "------------------------------------------------------\n";

            double lat, lon;
            std::cout << "[?] Enter Target Latitude (-90.0 to 90.0): ";
            std::cin >> lat;
            std::cout << "[?] Enter Target Longitude (-180.0 to 180.0): ";
            std::cin >> lon;

            Civilization nearest;
            double bestDist = std::numeric_limits<double>::max();

            nearestNeighbor(root, lat, lon, nearest, bestDist, 0);

            std::cout << "\n[!] Search Completed Successfully.\n";
            std::cout << "    Civilization Name    : " << nearest.name << "\n";
            std::cout << "    Location Coordinates : (" << nearest.latitude << ", " << nearest.longitude << ")\n";
            std::cout << "    Temporal Origin      : " << nearest.startYear << " CE\n";
            std::cout << "    Distance Delta       : " << bestDist << " units\n";
            std::cout << "------------------------------------------------------\n";
        }
        else if (choice == 2)
        {
            std::cout << "\n------------------------------------------------------\n";
            std::cout << "                 Range Query Search                 \n";
            std::cout << "------------------------------------------------------\n";

            double minLat, maxLat, minLon, maxLon;
            std::cout << "[?] Enter Minimum Latitude: ";
            std::cin >> minLat;
            std::cout << "[?] Enter Maximum Latitude: ";
            std::cin >> maxLat;
            std::cout << "[?] Enter Minimum Longitude: ";
            std::cin >> minLon;
            std::cout << "[?] Enter Maximum Longitude: ";
            std::cin >> maxLon;

            std::vector<Civilization> results;

            rangeSearch(root, minLat, maxLat, minLon, maxLon, 0, results);

            std::cout << "\n[!] Search Completed Successfully.\n";
            std::cout << "    Total Results Found: " << results.size() << " civilizations\n\n";

            if (!results.empty())
            {
                std::cout << std::left << std::setw(30) << "Civilization Name"
                          << "Coordinates (Lat, Lon)" << "\n";
                std::cout << "------------------------------------------------------\n";
                for (auto& c : results)
                {
                    std::cout << std::left << std::setw(30) << c.name
                              << "(" << c.latitude << ", " << c.longitude << ")\n";
                }
            }
            std::cout << "------------------------------------------------------\n";
        }
        else if (choice == 3)
        {
            std::cout << "\n------------------------------------------------------\n";
            std::cout << "               KD-Tree Structure View               \n";
            std::cout << "------------------------------------------------------\n";
            printKDTree(root, 0);
            std::cout << "------------------------------------------------------\n";
        }
        else if (choice == 4)
        {
            std::cout << "\n------------------------------------------------------\n";
            std::cout << "            Performance Benchmark Results           \n";
            std::cout << "------------------------------------------------------\n";
            benchmarkKDTree(root, civs);
            std::cout << "------------------------------------------------------\n";
        }
        else if (choice == 5)
        {
            Logger::info("Shutting down Spatial Intelligence System...");
            break;
        }
        else
        {
            Logger::warn("Unrecognized operation code. Please try again.");
        }
    }

    return 0;
}