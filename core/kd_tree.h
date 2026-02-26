#ifndef KD_TREE_H
#define KD_TREE_H

#include <string>
#include <vector>
#include <cmath>

struct Civilization {
    int id;
    std::string name;
    double latitude;
    double longitude;
    int startYear;
};

struct KDNode {
    Civilization civ;
    KDNode* left;
    KDNode* right;

    KDNode(Civilization c);
};

// KD-tree core APIs
KDNode* insertKD(KDNode* root, Civilization civ, int depth);
void printKDTree(KDNode* root, int depth);

// Query APIs
void rangeSearch(
    KDNode* root,
    double latMin,
    double latMax,
    double lonMin,
    double lonMax,
    int depth,
    std::vector<Civilization>& result
);

void nearestNeighbor(
    KDNode* root,
    double lat,
    double lon,
    Civilization& best,
    double& bestDist,
    int depth
);

double distance(double lat1, double lon1, double lat2, double lon2);

#endif