#include "time_filter.h"

std::vector<Civilization> filterByYearRange(
    const std::vector<Civilization>& data,
    int startYear,
    int endYear
) {
    std::vector<Civilization> result;

    for (const auto& civ : data) {
        if (civ.startYear >= startYear && civ.startYear <= endYear) {
            result.push_back(civ);
        }
    }

    return result;
}