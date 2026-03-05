# ============================================================
#  Civilization Spatial Intelligence Mapper — Makefile
#  Usage:
#    make        → compile
#    make run    → compile + run
#    make clean  → remove binary
# ============================================================

CXX      = g++
CXXFLAGS = -std=c++17 -Wall -O2
TARGET   = civilization_mapper
SRC      = civilization_mapper.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC)
	@echo "✅ Build successful → ./$(TARGET)"

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)
