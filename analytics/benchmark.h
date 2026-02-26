#pragma once
#include "../core/kd_tree.h"
#include "../data/csv_loader.h"
#include <vector>

void benchmarkKDTree(KDNode* root, const std::vector<Civilization>& civs);
