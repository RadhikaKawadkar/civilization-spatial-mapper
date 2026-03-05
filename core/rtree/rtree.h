#ifndef RTREE_H
#define RTREE_H

#include "../kd_tree.h" // For Civilization struct and distance function
#include <vector>
#include <algorithm>
#include <cmath>
#include <limits>
#include <iostream>
#include <memory>
#include <queue>

struct Point {
    double x, y;
    Civilization civ;
    
    // Exact equality for node delete operations
    bool operator==(const Point& other) const {
        return x == other.x && y == other.y && civ.id == other.civ.id;
    }
};

struct Rectangle {
    double xmin, ymin, xmax, ymax;

    Rectangle() : xmin(std::numeric_limits<double>::max()), ymin(std::numeric_limits<double>::max()),
                  xmax(std::numeric_limits<double>::lowest()), ymax(std::numeric_limits<double>::lowest()) {}

    Rectangle(double x1, double y1, double x2, double y2) : xmin(x1), ymin(y1), xmax(x2), ymax(y2) {}

    double area() const {
        if (xmin > xmax || ymin > ymax) return 0.0;
        return (xmax - xmin) * (ymax - ymin);
    }

    Rectangle combine(const Rectangle& other) const {
        return Rectangle(
            std::min(xmin, other.xmin),
            std::min(ymin, other.ymin),
            std::max(xmax, other.xmax),
            std::max(ymax, other.ymax)
        );
    }
    
    void expand(const Rectangle& other) {
        xmin = std::min(xmin, other.xmin);
        ymin = std::min(ymin, other.ymin);
        xmax = std::max(xmax, other.xmax);
        ymax = std::max(ymax, other.ymax);
    }

    bool intersects(const Rectangle& other) const {
        return !(xmin > other.xmax || xmax < other.xmin ||
                 ymin > other.ymax || ymax < other.ymin);
    }

    double enlargement(const Rectangle& other) const {
        Rectangle combined = combine(other);
        return combined.area() - area();
    }
    
    double distanceToPoint(double px, double py) const {
        double dx = std::max({0.0, xmin - px, px - xmax});
        double dy = std::max({0.0, ymin - py, py - ymax});
        return std::sqrt(dx * dx + dy * dy);
    }
    
    bool contains(const Point& p) const {
        return (p.x >= xmin && p.x <= xmax && p.y >= ymin && p.y <= ymax);
    }
};

class RTreeNode {
public:
    bool isLeaf;
    Rectangle mbr;
    RTreeNode* parent;
    
    // Replaced raw pointers with unique_ptr for strict modern C++17 memory safety
    std::vector<std::unique_ptr<RTreeNode>> children;
    std::vector<Point> points; // For leaf nodes only
    int maxChildren;

    // Default constructor taking parent non-owning raw pointer
    RTreeNode(bool leaf, int max_children, RTreeNode* parent_node = nullptr) 
        : isLeaf(leaf), parent(parent_node), maxChildren(max_children) {}

    // No need for explicit destructor, unique_ptr naturally cleans up all branches and stops memory leaks.
};

class RTree {
private:
    std::unique_ptr<RTreeNode> root;
    int MAX_CHILDREN;
    int MIN_CHILDREN;

    RTreeNode* chooseLeaf(RTreeNode* node, const Rectangle& r);
    std::unique_ptr<RTreeNode> splitNode(RTreeNode* node);
    void pickSeeds(RTreeNode* node, int& seed1, int& seed2);
    void distributeQuadratic(RTreeNode* node, std::unique_ptr<RTreeNode>& newNode, int seed1, int seed2);
    
    // Encapsulated MBR updating bounding functionality tightly
    void updateMBR(RTreeNode* node);
    
    // Upward tree adjustment via parent pointers
    void adjustTree(RTreeNode* node, std::unique_ptr<RTreeNode> splitNode);
    
    // Sub-routines for deletion maintaining R-Tree invariants
    RTreeNode* findLeaf(RTreeNode* node, const Point& point);
    void condenseTree(RTreeNode* node, std::vector<std::unique_ptr<RTreeNode>>& orphanedNodes, std::vector<Point>& orphanedPoints);
    
    void searchRec(RTreeNode* node, const Rectangle& query, std::vector<Civilization>& results) const;
    
public:
    RTree(int maxChildren);
    ~RTree();

    void insert(const Point& point);
    bool remove(const Point& point);
    std::vector<Civilization> search(const Rectangle& query) const;
    bool nearestNeighbor(const Point& point, Civilization& best, double& bestDist) const;
    void clear();
    int getHeight() const;
};

#endif
