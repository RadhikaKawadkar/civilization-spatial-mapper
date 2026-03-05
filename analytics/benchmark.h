#pragma once
#include "../core/kd_tree.h"
#include "../core/rtree/rtree.h"
#include "../data/csv_loader.h"
#include <vector>

void benchmarkTrees(KDNode* root, const RTree& rtree, const std::vector<Civilization>& civs);

void runSpatialScalingTest();
