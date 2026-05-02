"""
Lightweight R-Tree region index.
Stores named bounding boxes and answers point-in-region queries.
"""


class RTreeIndex:
    def __init__(self):
        self.regions: list[dict] = []

    def add_region(self, label: str, lat_min: float, lat_max: float,
                   lon_min: float, lon_max: float):
        self.regions.append({
            "label": label,
            "lat_min": lat_min, "lat_max": lat_max,
            "lon_min": lon_min, "lon_max": lon_max,
        })

    def add_default_regions(self):
        defaults = [
            ("South Asia",     5.0,  37.0,  60.0,  97.0),
            ("Mediterranean", 30.0,  45.0,  -5.0,  42.0),
            ("Middle East",   25.0,  40.0,  35.0,  60.0),
            ("East Asia",     20.0,  50.0,  95.0, 135.0),
            ("Mesoamerica",    5.0,  25.0,-110.0, -80.0),
            ("North Africa",  15.0,  35.0,  15.0,  50.0),
            ("Central Asia",  30.0,  55.0,  45.0, 120.0),
            ("South America",-25.0,   0.0, -80.0, -60.0),
        ]
        for label, lat_min, lat_max, lon_min, lon_max in defaults:
            self.add_region(label, lat_min, lat_max, lon_min, lon_max)

    def query_point(self, lat: float, lon: float) -> list[str]:
        return [
            r["label"] for r in self.regions
            if r["lat_min"] <= lat <= r["lat_max"]
            and r["lon_min"] <= lon <= r["lon_max"]
        ]
