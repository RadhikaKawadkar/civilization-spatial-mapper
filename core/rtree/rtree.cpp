#include "rtree.h"
#include <queue>
#include <cassert>

RTree::RTree(int maxChildren) : MAX_CHILDREN(maxChildren) {
    MIN_CHILDREN = std::max(2, MAX_CHILDREN / 2);
    root = std::make_unique<RTreeNode>(true, MAX_CHILDREN);
}

RTree::~RTree() {}

void RTree::clear() {
    root = std::make_unique<RTreeNode>(true, MAX_CHILDREN);
}

// ----------------------------------------------------
// Node MBR Update
// ----------------------------------------------------
void RTree::updateMBR(RTreeNode* node) {
    if (!node) return;
    
    node->mbr = Rectangle(); // Resets to inverted infinity boundaries
    if (node->isLeaf) {
        for (const auto& pt : node->points) {
            node->mbr.expand(Rectangle(pt.x, pt.y, pt.x, pt.y));
        }
    } else {
        for (const auto& child : node->children) {
            if (child) {
                node->mbr.expand(child->mbr);
            }
        }
    }
}

// ----------------------------------------------------
// Core Insert Algorithms
// ----------------------------------------------------
RTreeNode* RTree::chooseLeaf(RTreeNode* node, const Rectangle& r) {
    if (node->isLeaf) return node;

    double minEnlargement = std::numeric_limits<double>::max();
    double minArea = std::numeric_limits<double>::max();
    RTreeNode* bestChild = nullptr;
    
    for (auto& child : node->children) {
        double enlargement = child->mbr.enlargement(r);
        if (enlargement < minEnlargement) {
            minEnlargement = enlargement;
            bestChild = child.get();
            minArea = child->mbr.area();
        } else if (enlargement == minEnlargement) {
            // Prune tied nodes by minimum original area
            if (child->mbr.area() < minArea) {
                minArea = child->mbr.area();
                bestChild = child.get();
            }
        }
    }

    if (!bestChild) bestChild = node->children[0].get(); 
    return chooseLeaf(bestChild, r);
}

// Picks furthest pair via maximizing rectangular inefficiency
void RTree::pickSeeds(RTreeNode* node, int& seed1, int& seed2) {
    double maxInefficiency = -std::numeric_limits<double>::max();
    seed1 = 0;
    seed2 = 1;

    size_t count = node->isLeaf ? node->points.size() : node->children.size();
    
    for (size_t i = 0; i < count; ++i) {
        for (size_t j = i + 1; j < count; ++j) {
            Rectangle rect1, rect2;
            
            if (node->isLeaf) {
                rect1 = Rectangle(node->points[i].x, node->points[i].y, node->points[i].x, node->points[i].y);
                rect2 = Rectangle(node->points[j].x, node->points[j].y, node->points[j].x, node->points[j].y);
            } else {
                rect1 = node->children[i]->mbr;
                rect2 = node->children[j]->mbr;
            }

            Rectangle combined = rect1.combine(rect2);
            double inefficiency = combined.area() - rect1.area() - rect2.area();
            if (inefficiency > maxInefficiency) {
                maxInefficiency = inefficiency;
                seed1 = i;
                seed2 = j;
            }
        }
    }
}

void RTree::distributeQuadratic(RTreeNode* node, std::unique_ptr<RTreeNode>& newNode, int seed1, int seed2) {
    if (node->isLeaf) {
        std::vector<Point> original;
        std::swap(node->points, original);
        
        node->points.push_back(original[seed1]);
        newNode->points.push_back(original[seed2]);
        updateMBR(node);
        updateMBR(newNode.get());
        
        for (size_t i = 0; i < original.size(); ++i) {
            if (i == seed1 || i == seed2) continue;
            
            Rectangle ptRect(original[i].x, original[i].y, original[i].x, original[i].y);
            double enl1 = node->mbr.enlargement(ptRect);
            double enl2 = newNode->mbr.enlargement(ptRect);
            
            if (enl1 < enl2 || (enl1 == enl2 && node->mbr.area() <= newNode->mbr.area())) {
                node->points.push_back(original[i]);
                updateMBR(node);
            } else {
                newNode->points.push_back(original[i]);
                updateMBR(newNode.get());
            }
        }
    } else {
        std::vector<std::unique_ptr<RTreeNode>> original;
        std::swap(node->children, original);
        
        node->children.push_back(std::move(original[seed1]));
        newNode->children.push_back(std::move(original[seed2]));
        
        node->children.back()->parent = node;
        newNode->children.back()->parent = newNode.get();
        updateMBR(node);
        updateMBR(newNode.get());
        
        for (size_t i = 0; i < original.size(); ++i) {
            if (i == seed1 || i == seed2 || !original[i]) continue;
            
            Rectangle childMBR = original[i]->mbr;
            double enl1 = node->mbr.enlargement(childMBR);
            double enl2 = newNode->mbr.enlargement(childMBR);
            
            if (enl1 < enl2 || (enl1 == enl2 && node->mbr.area() <= newNode->mbr.area())) {
                original[i]->parent = node;
                node->children.push_back(std::move(original[i]));
                updateMBR(node);
            } else {
                original[i]->parent = newNode.get();
                newNode->children.push_back(std::move(original[i]));
                updateMBR(newNode.get());
            }
        }
    }
}

std::unique_ptr<RTreeNode> RTree::splitNode(RTreeNode* node) {
    auto newNode = std::make_unique<RTreeNode>(node->isLeaf, MAX_CHILDREN, node->parent);
    int seed1, seed2;
    pickSeeds(node, seed1, seed2);
    distributeQuadratic(node, newNode, seed1, seed2);
    return newNode;
}

// Resolves splits and expansions upwards using raw parent mappings sequentially (no stack tracking)
void RTree::adjustTree(RTreeNode* node, std::unique_ptr<RTreeNode> splitNode) {
    while (node != root.get()) {
        RTreeNode* parent = node->parent;
        updateMBR(parent);
        
        if (splitNode) { // Sub-tree splitted, join the new leaf to the parent
            splitNode->parent = parent;
            parent->children.push_back(std::move(splitNode));
            updateMBR(parent);
            if (parent->children.size() > MAX_CHILDREN) {
                splitNode = RTree::splitNode(parent);
            } else {
                splitNode = nullptr;
            }
        }
        node = parent;
    }
    
    // Expand root vertically
    if (splitNode) {
        auto newRoot = std::make_unique<RTreeNode>(false, MAX_CHILDREN, nullptr);
        node->parent = newRoot.get();
        splitNode->parent = newRoot.get();
        newRoot->children.push_back(std::move(root));
        newRoot->children.push_back(std::move(splitNode));
        updateMBR(newRoot.get());
        root = std::move(newRoot);
    }
}

void RTree::insert(const Point& point) {
    Rectangle r(point.x, point.y, point.x, point.y);
    RTreeNode* leaf = chooseLeaf(root.get(), r);
    
    leaf->points.push_back(point);
    updateMBR(leaf);
    
    std::unique_ptr<RTreeNode> splitPhase = nullptr;
    if (leaf->points.size() > MAX_CHILDREN) {
        splitPhase = splitNode(leaf);
    }
    
    adjustTree(leaf, std::move(splitPhase));
}

// ----------------------------------------------------
// FULL DELETE IMPLEMENTATION
// ----------------------------------------------------

RTreeNode* RTree::findLeaf(RTreeNode* node, const Point& point) {
    if (!node || !node->mbr.contains(point)) return nullptr;
    
    if (node->isLeaf) {
        for (const auto& pt : node->points) {
            if (pt == point) return node;
        }
        return nullptr;
    }
    
    for (auto& child : node->children) {
        RTreeNode* result = findLeaf(child.get(), point);
        if (result) return result;
    }
    return nullptr;
}

void RTree::condenseTree(RTreeNode* node, std::vector<std::unique_ptr<RTreeNode>>& orphanedNodes, std::vector<Point>& orphanedPoints) {
    while (node != root.get()) {
        RTreeNode* parent = node->parent;
        
        // Is node under threshold limits? 
        bool underflow = (node->isLeaf && node->points.size() < MIN_CHILDREN) || 
                         (!node->isLeaf && node->children.size() < MIN_CHILDREN);
                         
        if (underflow) {
            auto it = std::find_if(parent->children.begin(), parent->children.end(),
                                   [node](const std::unique_ptr<RTreeNode>& ptr) { return ptr.get() == node; });
            if (it != parent->children.end()) {
                if (node->isLeaf) {
                    for (const auto& pt : node->points) orphanedPoints.push_back(pt);
                } else {
                    for (auto& child : node->children) orphanedNodes.push_back(std::move(child));
                }
                parent->children.erase(it); // Drop node!
            }
        }
        
        updateMBR(parent);
        node = parent;
    }
}

bool RTree::remove(const Point& point) {
    RTreeNode* leaf = findLeaf(root.get(), point);
    if (!leaf) return false;
    
    // Excise entry natively
    auto it = std::find_if(leaf->points.begin(), leaf->points.end(),
                           [&](const Point& p) { return p == point; });
    if (it != leaf->points.end()) {
        leaf->points.erase(it);
    } else {
        return false;
    }
    
    updateMBR(leaf);
    
    std::vector<std::unique_ptr<RTreeNode>> orphanedNodes;
    std::vector<Point> orphanedPoints;
    
    condenseTree(leaf, orphanedNodes, orphanedPoints);
    
    // Fully de-construct sub-hierachies to avoid height imbalance issues recursively
    auto extractPointsRec = [&](RTreeNode* n, auto& extractRef) -> void {
        if (n->isLeaf) {
            for (const auto& pt : n->points) orphanedPoints.push_back(pt);
        } else {
            for (auto& child : n->children) extractRef(child.get(), extractRef);
        }
    };
    
    for (auto& node : orphanedNodes) {
        if (node) extractPointsRec(node.get(), extractPointsRec);
    }
    
    // Top-down reinsertion to recover structure properly
    for (const auto& pt : orphanedPoints) {
        insert(pt);
    }

    // Retract heights if singular internal route exists via condensing
    if (!root->isLeaf && root->children.size() == 1) {
        std::unique_ptr<RTreeNode> newRoot = std::move(root->children[0]);
        newRoot->parent = nullptr;
        root = std::move(newRoot);
    }
    return true;
}

// ----------------------------------------------------
// QUERY & PERFORMANCE OPTIMIZATIONS
// ----------------------------------------------------

void RTree::searchRec(RTreeNode* node, const Rectangle& query, std::vector<Civilization>& results) const {
    if (!node || !node->mbr.intersects(query)) return;

    if (node->isLeaf) {
        for (const auto& point : node->points) {
            if (query.contains(point)) {
                results.push_back(point.civ);
            }
        }
    } else {
        for (auto& child : node->children) {
            searchRec(child.get(), query, results);
        }
    }
}

std::vector<Civilization> RTree::search(const Rectangle& query) const {
    std::vector<Civilization> results;
    searchRec(root.get(), query, results);
    return results;
}


// Performance Priority Queue Sorting Object Minimum Distances efficiently
struct NNPriNode {
    double dist;
    RTreeNode* node;
    bool operator>(const NNPriNode& other) const { return dist > other.dist; }
};

bool RTree::nearestNeighbor(const Point& point, Civilization& best, double& bestDist) const {
    bestDist = std::numeric_limits<double>::max();
    bool found = false;

    // Ordered Minimum Distance Search
    std::priority_queue<NNPriNode, std::vector<NNPriNode>, std::greater<NNPriNode>> pq;
    pq.push({root->mbr.distanceToPoint(point.x, point.y), root.get()});

    while (!pq.empty()) {
        auto current = pq.top();
        pq.pop();

        // Safe bounds prune avoiding O(n) scan
        if (current.dist >= bestDist) break; 

        RTreeNode* node = current.node;
        if (node->isLeaf) {
            for (const auto& pt : node->points) {
                double d = distance(point.y, point.x, pt.civ.latitude, pt.civ.longitude);
                if (d < bestDist) {
                    bestDist = d;
                    best = pt.civ;
                    found = true;
                }
            }
        } else {
            for (auto& child : node->children) {
                double minDist = child->mbr.distanceToPoint(point.x, point.y);
                // Child minimum distance optimization before enqueue
                if (minDist < bestDist) {
                    pq.push({minDist, child.get()});
                }
            }
        }
    }
    return found;
}

int RTree::getHeight() const {
    if (!root) return 0;
    int height = 1;
    RTreeNode* curr = root.get();
    while (curr && !curr->isLeaf) {
        height++;
        curr = curr->children.empty() ? nullptr : curr->children[0].get();
    }
    return height;
}
