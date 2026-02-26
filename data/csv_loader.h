#ifndef CSV_LOADER_H
#define CSV_LOADER_H

#include <vector>
#include <string>
#include "../core/kd_tree.h"

std::vector<Civilization> loadCivilizations(const std::string& filename);

#endif