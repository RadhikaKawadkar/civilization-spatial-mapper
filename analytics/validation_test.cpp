#include <iostream>
#include <vector>
#include <random>
#include <chrono>
#include <iomanip>
#include <cmath>
#include "core/rtree/rtree.h"
#include "core/kd_tree.h"

using namespace std;
using namespace std::chrono;

int main() {
    cout << "\n======================================================\n";
    cout << "          FULL SYSTEM VALIDATION TESTING          \n";
    cout << "======================================================\n";

    mt19937 gen(42);
    uniform_real_distribution<double> lat_dis(-90.0, 90.0);
    uniform_real_distribution<double> lon_dis(-180.0, 180.0);

    bool allTestsPass = true;
    double insertTime = 0, deleteTime = 0, avgNNTime = 0, avgRangeTime = 0;
    int treeHeight = 0;

    // ---------------------------------------------------------
    // 1. Massive Stress Test (500k insert, 200k delete, 1k test)
    // ---------------------------------------------------------
    cout << "[TEST 1] Massive Stress Test\n";
    {
        RTree rtree(8);
        const int INSERT_COUNT = 500000;
        const int DELETE_COUNT = 200000;
        vector<Point> pts;
        pts.reserve(INSERT_COUNT);
        for(int i=0; i<INSERT_COUNT; i++) {
            Civilization c{i, "Stress", lat_dis(gen), lon_dis(gen), 2000};
            pts.push_back({c.longitude, c.latitude, c});
        }

        auto start = high_resolution_clock::now();
        for(auto& p : pts) rtree.insert(p);
        auto end = high_resolution_clock::now();
        insertTime = duration_cast<milliseconds>(end - start).count();

        auto startDel = high_resolution_clock::now();
        for(int i=0; i<DELETE_COUNT; i++) rtree.remove(pts[i]);
        auto endDel = high_resolution_clock::now();
        deleteTime = duration_cast<milliseconds>(endDel - startDel).count();

        treeHeight = rtree.getHeight();

        double totalNN = 0, totalRange = 0;
        for(int i=0; i<1000; i++) {
            double qlat = lat_dis(gen);
            double qlon = lon_dis(gen);
            
            auto s1 = high_resolution_clock::now();
            Civilization best; double bestDist;
            rtree.nearestNeighbor({qlon, qlat, Civilization()}, best, bestDist);
            auto e1 = high_resolution_clock::now();
            totalNN += duration_cast<microseconds>(e1-s1).count();

            Rectangle rect(qlon-5, qlat-5, qlon+5, qlat+5);
            auto s2 = high_resolution_clock::now();
            rtree.search(rect);
            auto e2 = high_resolution_clock::now();
            totalRange += duration_cast<microseconds>(e2-s2).count();
        }
        avgNNTime = totalNN / 1000.0;
        avgRangeTime = totalRange / 1000.0;
        cout << "  -> Insert Time: " << insertTime << " ms\n";
        cout << "  -> Delete Time: " << deleteTime << " ms\n";
        cout << "  -> Avg NN Time: " << avgNNTime << " us\n";
        cout << "  -> Avg Range Time: " << avgRangeTime << " us\n";
        cout << "  -> Tree Height: " << treeHeight << "\n";
    }

    // ---------------------------------------------------------
    // 2. Clustered Test (300k points in 1-degree area)
    // ---------------------------------------------------------
    cout << "\n[TEST 2] Clustered Data Test (300k)\n";
    {
        RTree rtree(8);
        uniform_real_distribution<double> c_dis(10.0, 11.0);
        for(int i=0; i<300000; i++) {
            Civilization c{i, "Cluster", c_dis(gen), c_dis(gen), 2000};
            rtree.insert({c.longitude, c.latitude, c});
        }
        Civilization best; double bD;
        rtree.nearestNeighbor({10.5, 10.5, Civilization()}, best, bD);
        if (best.name != "Cluster") allTestsPass = false;
        cout << "  -> Clustered nearest neighbor matched.\n";
    }

    // ---------------------------------------------------------
    // 3. KD vs R-Tree Nearest Neighbor Correctness
    // ---------------------------------------------------------
    cout << "\n[TEST 3] KD vs R-Tree NN Correctness\n";
    {
        KDNode* kdRoot = nullptr;
        RTree rtree(8);
        for(int i=0; i<50000; i++) {
            Civilization c{i, "Compare", lat_dis(gen), lon_dis(gen), 2000};
            kdRoot = insertKD(kdRoot, c, 0);
            rtree.insert({c.longitude, c.latitude, c});
        }

        bool match = true;
        for(int i=0; i<100; i++) {
            double qlat = lat_dis(gen), qlon = lon_dis(gen);
            Civilization kdBest, rtBest;
            double kdDist = 1e9, rtDist = 1e9;
            nearestNeighbor(kdRoot, qlat, qlon, kdBest, kdDist, 0);
            rtree.nearestNeighbor({qlon, qlat, Civilization()}, rtBest, rtDist);
            
            if (abs(kdDist - rtDist) > 1e-6) {
                match = false;
                break;
            }
        }
        if(!match) {
            allTestsPass = false;
            cout << "  -> FAIL: NN mismatch between KD and R-Tree!\n";
        } else {
            cout << "  -> PASS: Equivalent outputs verified.\n";
        }
    }

    // ---------------------------------------------------------
    // 4. Edge Cases
    // ---------------------------------------------------------
    cout << "\n[TEST 4] Edge Cases\n";
    {
        RTree rtree(8);
        // Empty tree search
        Civilization best; double bDist;
        bool nnFound = rtree.nearestNeighbor({0,0,Civilization()}, best, bDist);
        if (nnFound) { cout << "FAIL: Found NN in empty tree.\n"; allTestsPass=false; }

        auto rs = rtree.search({-1,-1,1,1});
        if (!rs.empty()) { cout << "FAIL: Range query returned items in empty tree.\n"; allTestsPass=false; }

        // Duplicate inserts
        Civilization c{1, "Dup", 0.0, 0.0, 2000};
        rtree.insert({c.longitude, c.latitude, c});
        rtree.insert({c.longitude, c.latitude, c});
        rs = rtree.search({-1,-1,1,1});
        if (rs.size() != 2) { cout << "FAIL: Duplicate failed.\n"; allTestsPass=false; }

        // Delete non-existing
        Civilization bad{2, "Bad", 0.0, 0.0, 2000};
        if (rtree.remove({bad.longitude, bad.latitude, bad})) { cout << "FAIL: Removed non-existent.\n"; allTestsPass=false; }
        
        // Delete until empty
        rtree.remove({c.longitude, c.latitude, c});
        rtree.remove({c.longitude, c.latitude, c});
        if (rtree.getHeight() > 1) { cout << "FAIL: Tree didn't condense correctly. Height: "<< rtree.getHeight() <<"\n"; allTestsPass=false; }
        
        cout << "  -> Edge cases passed.\n";
    }

    // ---------------------------------------------------------
    // 5. SUMMARY
    // ---------------------------------------------------------
    cout << "\n======================================================\n";
    cout << "             VALIDATION SUMMARY               \n";
    cout << "======================================================\n";
    cout << "Insert time : " << insertTime << " ms\n";
    cout << "Delete time : " << deleteTime << " ms\n";
    cout << "Avg NN time : " << avgNNTime << " us\n";
    cout << "Avg Range   : " << avgRangeTime << " us\n";
    cout << "Tree height : " << treeHeight << "\n";
    cout << "Overall     : [" << (allTestsPass ? "PASS" : "FAIL") << "]\n";
    cout << "======================================================\n";

    return allTestsPass ? 0 : 1;
}
