"""
Data models shared across the backend.
"""


class Civilization:
    def __init__(self, name, lat, lon, start=0, end=0, region="",
                 resource=50.0, knowledge=50.0, military=50.0):
        self.name = name
        self.latitude = float(lat)
        self.longitude = float(lon)
        self.start_year = int(start)
        self.end_year = int(end)
        self.region = region
        self.resource_density = float(resource)
        self.knowledge_density = float(knowledge)
        self.military_strength = float(military)

    def spatial_score(self) -> float:
        return round(
            (self.resource_density + self.knowledge_density + self.military_strength) / 3, 2
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "region": self.region,
            "resource_density": self.resource_density,
            "knowledge_density": self.knowledge_density,
            "military_strength": self.military_strength,
            "spatial_score": self.spatial_score(),
        }


class ClusterResult:
    def __init__(self, civ: Civilization, cluster_id: int):
        self.civ = civ
        self.cluster_id = cluster_id  # -1 = noise

    def to_dict(self) -> dict:
        d = self.civ.to_dict()
        d["cluster_id"] = self.cluster_id
        return d
