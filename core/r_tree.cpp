#include "r_tree.h"

void RTree::insert(Rect r) {
    nodes.push_back(r);
}

std::vector<Rect> RTree::rangeQuery(
    double minLat, double maxLat,
    double minLon, double maxLon
) {
    std::vector<Rect> result;

    for (auto& r : nodes) {
        if (!(r.maxLat < minLat || r.minLat > maxLat ||
              r.maxLon < minLon || r.minLon > maxLon)) {
            result.push_back(r);
        }
    }
    return result;
}