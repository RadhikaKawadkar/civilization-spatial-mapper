#include "kd_tree.h"
#include <iostream>

KDNode::KDNode(Civilization c) : civ(c), left(nullptr), right(nullptr) {}

double distance(double lat1, double lon1, double lat2, double lon2) {
    return sqrt(pow(lat1 - lat2, 2) + pow(lon1 - lon2, 2));
}

KDNode* insertKD(KDNode* root, Civilization civ, int depth) {
    if (!root)
        return new KDNode(civ);

    int cd = depth % 2;

    if ((cd == 0 && civ.latitude < root->civ.latitude) ||
        (cd == 1 && civ.longitude < root->civ.longitude))
        root->left = insertKD(root->left, civ, depth + 1);
    else
        root->right = insertKD(root->right, civ, depth + 1);

    return root;
}

void printKDTree(KDNode* root, int depth) {
    if (!root) return;

    for (int i = 0; i < depth; i++) std::cout << "  ";
    std::cout << root->civ.name
              << " (" << root->civ.latitude
              << ", " << root->civ.longitude << ")\n";

    printKDTree(root->left, depth + 1);
    printKDTree(root->right, depth + 1);
}

void rangeSearch(
    KDNode* root,
    double latMin,
    double latMax,
    double lonMin,
    double lonMax,
    int depth,
    std::vector<Civilization>& result
) {
    if (!root) return;

    if (root->civ.latitude >= latMin &&
        root->civ.latitude <= latMax &&
        root->civ.longitude >= lonMin &&
        root->civ.longitude <= lonMax) {
        result.push_back(root->civ);
    }

    int cd = depth % 2;

    if ((cd == 0 && latMin < root->civ.latitude) ||
        (cd == 1 && lonMin < root->civ.longitude))
        rangeSearch(root->left, latMin, latMax, lonMin, lonMax, depth + 1, result);

    if ((cd == 0 && latMax >= root->civ.latitude) ||
        (cd == 1 && lonMax >= root->civ.longitude))
        rangeSearch(root->right, latMin, latMax, lonMin, lonMax, depth + 1, result);
}

void nearestNeighbor(
    KDNode* root,
    double lat,
    double lon,
    Civilization& best,
    double& bestDist,
    int depth
) {
    if (!root) return;

    double d = distance(lat, lon, root->civ.latitude, root->civ.longitude);
    if (d < bestDist) {
        bestDist = d;
        best = root->civ;
    }

    int cd = depth % 2;
    KDNode* nearBranch;
    KDNode* farBranch;

    if ((cd == 0 && lat < root->civ.latitude) ||
        (cd == 1 && lon < root->civ.longitude)) {
        nearBranch = root->left;
        farBranch = root->right;
    } else {
        nearBranch = root->right;
        farBranch = root->left;
    }

    nearestNeighbor(nearBranch, lat, lon, best, bestDist, depth + 1);

    double diff = (cd == 0)
                    ? abs(lat - root->civ.latitude)
                    : abs(lon - root->civ.longitude);

    if (diff < bestDist)
        nearestNeighbor(farBranch, lat, lon, best, bestDist, depth + 1);
}