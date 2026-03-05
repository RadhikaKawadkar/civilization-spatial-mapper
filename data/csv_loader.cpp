#include "csv_loader.h"
#include <fstream>
#include <sstream>
#include <iostream>

std::vector<Civilization> loadCivilizations(const std::string& filename) {
    std::vector<Civilization> civs;
    std::ifstream file(filename);

    if (!file.is_open()) {
        std::cout << "Error opening CSV file\n";
        return civs;
    }

    std::string line;
    getline(file, line); // header

    while (getline(file, line)) {
        std::stringstream ss(line);
        Civilization c;
        std::string temp;

        getline(ss, temp, ','); c.id = stoi(temp);
        getline(ss, c.name, ',');
        getline(ss, temp, ','); c.latitude = stod(temp);
        getline(ss, temp, ','); c.longitude = stod(temp);
        getline(ss, temp, ','); c.startYear = stoi(temp);

        civs.push_back(c);
    }

    file.close();
    return civs;
}