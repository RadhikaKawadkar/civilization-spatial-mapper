cmake_minimum_required(VERSION 3.10)
project(CivilizationSpatialMapper)

set(CMAKE_CXX_STANDARD 17)

add_executable(app
    main.cpp
    core/kd_tree.cpp
    core/r_tree.cpp
    data/csv_loader.cpp
    analytics/performance.cpp
)
