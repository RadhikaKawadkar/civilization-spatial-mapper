#ifndef R_TREE_H
#define R_TREE_H

#include <vector>
#include <string>

struct Rect {
    double minLat, maxLat;
    double minLon, maxLon;
    std::string name;
};

class RTree {
private:
    std::vector<Rect> nodes;

public:
    void insert(Rect r);
    std::vector<Rect> rangeQuery(
        double minLat, double maxLat,
        double minLon, double maxLon
    );
};

#endif