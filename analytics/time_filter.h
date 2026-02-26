#ifndef TIME_FILTER_H
#define TIME_FILTER_H

#include <vector>
#include "../core/kd_tree.h"

std::vector<Civilization> filterByYearRange(
    const std::vector<Civilization>& data,
    int startYear,
    int endYear
);

#endif