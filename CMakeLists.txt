cmake_minimum_required(VERSION 3.10)
project(CivilizationSpatialMapper)

set(CMAKE_CXX_STANDARD 17)

add_executable(spatial_mapper
    main.cpp
    core/kd_tree.cpp
    core/rtree/rtree.cpp
    utils/logger.cpp
    data/csv_loader.cpp
    analytics/benchmark.cpp
    analytics/spatial_scaling_test.cpp
)
