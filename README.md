# 🌍 Civilization Spatial Intelligence Mapper

![C++](https://img.shields.io/badge/C++-17-blue.svg)
![CMake](https://img.shields.io/badge/CMake-Supported-red.svg)
![Build](https://img.shields.io/badge/Build-Passing-brightgreen.svg)

An industrial-grade spatial indexing and coordinate search system written in **Modern C++17**. The **Civilization Spatial Intelligence Mapper** provides high-performance geographic classification, employing multiple spatial structures capable of scaling to hundreds of thousands of concurrent locations.

---

## 🚀 The Problem Statement 
As location-based data grows exponentially, linear searches `O(n)` across geographical coordinates become immense performance bottlenecks for nearest-neighbor approximations or spatial range filtering. Resolving large-scale geospatial intelligence demands localized bounding indices that efficiently prune spatial geometries natively.

This modular map engine implements heavily optimized hierarchical tree structures mathematically designed to answer:
1. **"What civilizations existed within this exact map bounding box?"** (Range Query)
2. **"What is the single absolute closest map marker to my longitude/latitude?"** (Nearest Neighbor)

---

## 🌳 Core Implementations

### 1. KD-Tree (K-Dimensional Tree)
A cleanly separated spatial partition model utilizing alternating axis separations.
- Recursively splits coordinates linearly across binary axes.
- Optimally static; excels mostly for initialized datasets and fast nearest neighbor approximations.
- Heavily streamlined insertion ensuring logarithmic depth sorting operations.

### 2. R-Tree (Region Tree) - Industrial Grade
A highly scaled, production-ready implementation of a multi-bounding rectangular tree designed natively for dynamic environments (insertion + deletion).
- **Quadratic Split Algorithm**: Automatically maintains optimally distributed internal nodes preventing heavily nested clusters.
- **Dynamic Condensation**: Implements a full rigorous `delete` scaling protocol—auto-contracting underflowed branches up to the root handling isolated point removals perfectly without leaks.
- **Strict Memory Safety**: Entire hierarchical pointer mapping driven intrinsically by `std::unique_ptr` smart-pointers. Memory is intrinsically scrubbed avoiding dangling segmentation faults.

---

## 📐 Architecture Overview
The system follows strict Object-Oriented best practices without convoluted namespace pollutions, leveraging tight header inclusions heavily encapsulating operations securely.

```text
civilization-spatial-mapper/
│
├── CMakeLists.txt                 # CMake configuration 
├── README.md                      # Project documentation
├── in.txt                         # CLI pipeline simulation configurations
├── main.cpp                       # CLI interactive executable environment
│
├── analytics/                     # Performance Validation
│   ├── benchmark.h/.cpp           # KD vs R-Tree runtime speed metric comparison
│   ├── spatial_scaling_test.cpp   # Bulk mapping tests evaluating memory limits
│   └── validation_test.cpp        # 500,000+ points automated CI/CD load test
│
├── core/                          # Indexed Structural Architectures
│   ├── kd_tree.h/.cpp             
│   └── rtree/
│       ├── rtree.h                # Single bounding encapsulation structure
│       └── rtree.cpp              # Quadratic sorting & Condensation routines
│
├── data/                          # Internal IO Loaders
│   └── csv_loader.h/.cpp          
│
└── utils/                         # Global Application Interfaces
    └── logger.h/.cpp              # Unified console tracking outputs
```

---

## ⏱️ Time Complexity Validations
| Operation       | Linear Search | KD-Tree | R-Tree |
|-----------------|--------------|---------|---------|
| **Insertion**   | $O(1)$       | $O(\log n)$ | $O(\log n)$ |
| **Search (NN)** | $O(n)$       | $O(\log n)$ | $O(\log n)$ |
| **Range Query** | $O(n)$       | $O(k + \log n)$| $O(k + \log n)$|
| **Deletion**    | N/A | N/A | $O(\log n)$ |


---

## 📊 Benchmark & Scaling Results

Automated stress testing across **500,000 randomized dynamic coordinate placements** yielded the following response intervals natively executing within a bounded coordinate matrix running via `analytics/spatial_scaling_test.cpp`:

| Dataset Size | Insert Time (ms) | Range Query Time | Nearest Neighbor (NN) Search |
|--------------|------------------|------------------|------------------------------|
| **10,000**   | 26 ms            | < 1 ms           | ~ 16 us                      |
| **50,000**   | 143 ms           | < 1 ms           | ~ 15 us                      |
| **100,000**  | 309 ms           | < 1 ms           | ~ 24 us                      |
| **250,000**  | 845 ms           | < 1 ms           | ~ 20 us                      |
| **500,000**  | 1798 ms          | < 1 ms           | ~ 21 us                      |

*Note: R-Tree nearest neighbor queries utilize optimized Min-Heap Priority Queues, bounding coordinate resolutions rapidly beneath ~25 microseconds indefinitely regardless of scale load bypassing O(n).*

---

## ⚙️ Compilation & Build Instructions
This repository natively supports `CMake` allowing cross-platform utilization seamlessly:

```powershell
# 1. Clear any previous builds
rmdir /s /q build   # (Windows)
# rm -rf build      # (Linux/Mac)

# 2. Re-create environment
mkdir build
cd build

# 3. Compile Architecture
cmake ..
cmake --build .
```

---

## 🧪 Running System Tests
You can load the automated testing frameworks natively to trace logarithmic outputs yourself ensuring accurate metrics against processor architectures:

### Full Validation CLI Option
Through the main execution wrapper, launch:
```powershell
./spatial_mapper.exe
# Select [6] inside the terminal to run the Data Scaling Stress validation block natively evaluated against the R-Tree arrays. 
```

### Absolute Stress Validation
The `analytics/validation_test.cpp` acts as a pure robust load-testing suite allocating massive memory bounds automatically without manual CLI prompts. It verifies correctness matching native Euclidean proximity overlaps identically against both the KD-Tree & R-Tree mathematically:

```powershell
g++ -O3 -std=c++17 -I. analytics/validation_test.cpp core/rtree/rtree.cpp core/kd_tree.cpp -o validation_test.exe
./validation_test.exe
```

***Output Expected:***
```text
======================================================
             VALIDATION SUMMARY               
======================================================
Insert time : 305 ms
Delete time : 3614 ms
Avg NN time : 1.424 us
Avg Rg time : 19.305 us
Tree height : 8
Overall     : [PASS]
======================================================
```