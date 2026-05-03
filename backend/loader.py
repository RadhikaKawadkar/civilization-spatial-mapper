"""
Data loader — reads civilizations.csv (rich format) or final_dataset.csv (minimal format).
Falls back to built-in enriched data if neither file is found.
"""

import csv
import os
from models import Civilization

# Full enriched dataset — 47 Indian/South Asian civilizations with scores
BUILTIN: list[tuple] = [
    ("Indus Valley (Harappan)",   25.0,  67.0, -2600, -1900, "South Asia",   88, 85, 60),
    ("Early Harappan",            28.0,  70.0, -3300, -2600, "South Asia",   82, 80, 55),
    ("Late Harappan",             27.0,  68.0, -1900, -1300, "South Asia",   78, 75, 52),
    ("Vedic Civilization",        28.5,  77.0, -1500,  -600, "South Asia",   75, 92, 70),
    ("Painted Grey Ware Culture", 29.0,  77.5, -1200,  -600, "South Asia",   70, 72, 60),
    ("Mahajanapadas",             25.0,  85.0,  -600,  -321, "South Asia",   78, 85, 75),
    ("Magadha",                   25.2,  86.0,  -600,  -321, "South Asia",   80, 88, 82),
    ("Maurya Empire",             25.6,  85.1,  -322,  -185, "South Asia",   85, 88, 85),
    ("Shunga Dynasty",            25.0,  82.0,  -185,   -73, "South Asia",   72, 78, 70),
    ("Kanva Dynasty",             25.0,  82.0,   -73,    28, "South Asia",   68, 74, 65),
    ("Satavahana Dynasty",        19.0,  78.0,  -100,   220, "South Asia",   80, 82, 78),
    ("Indo-Greek Kingdom",        34.0,  72.0,  -180,    10, "South Asia",   75, 80, 78),
    ("Kushan Empire",             34.5,  71.0,    50,   375, "Central Asia", 82, 80, 85),
    ("Western Kshatrapas",        22.5,  72.0,    35,   415, "South Asia",   70, 72, 72),
    ("Gupta Empire",              23.0,  77.0,   320,   550, "South Asia",   85, 95, 78),
    ("Vakataka Dynasty",          20.5,  79.0,   250,   500, "South Asia",   74, 80, 72),
    ("Maitraka Dynasty",          22.3,  72.6,   475,   767, "South Asia",   72, 75, 70),
    ("Chalukya Dynasty",          15.5,  75.0,   543,   753, "South India",  78, 82, 80),
    ("Rashtrakuta Dynasty",       16.0,  75.5,   753,   982, "South India",  79, 84, 83),
    ("Pallava Dynasty",           12.8,  80.2,   275,   897, "South India",  78, 87, 80),
    ("Chola Dynasty",             10.8,  79.1,   300,  1279, "South India",  82, 88, 86),
    ("Pandya Dynasty",             9.9,  78.1,   300,  1345, "South India",  76, 82, 74),
    ("Chera Dynasty",             10.3,  76.3,   300,  1102, "South India",  80, 82, 72),
    ("Hoysala Empire",            13.0,  76.1,  1026,  1343, "South India",  78, 85, 76),
    ("Kakatiya Dynasty",          18.0,  79.6,  1083,  1323, "South India",  76, 80, 78),
    ("Seuna (Yadava) Dynasty",    19.9,  73.8,   850,  1334, "South Asia",   74, 78, 76),
    ("Paramara Dynasty",          23.5,  75.8,   800,  1305, "South Asia",   72, 76, 74),
    ("Chandela Dynasty",          24.8,  79.9,   831,  1315, "South Asia",   74, 80, 76),
    ("Gurjara-Pratihara",         27.0,  73.0,   730,  1036, "South Asia",   76, 78, 80),
    ("Pala Empire",               24.0,  88.0,   750,  1161, "South Asia",   77, 90, 76),
    ("Sena Dynasty",              23.0,  89.0,  1097,  1230, "South Asia",   72, 80, 72),
    ("Ahom Kingdom",              26.5,  92.7,  1228,  1826, "South Asia",   74, 76, 82),
    ("Kamarupa Kingdom",          26.0,  91.8,   350,  1140, "South Asia",   72, 74, 70),
    ("Kashmir Shaiva Kingdoms",   34.1,  74.8,   800,  1339, "South Asia",   70, 88, 68),
    ("Delhi Sultanate",           28.6,  77.2,  1206,  1526, "South Asia",   76, 72, 88),
    ("Bahmani Sultanate",         17.0,  76.8,  1347,  1527, "South Asia",   74, 74, 80),
    ("Vijayanagara Empire",       15.3,  76.5,  1336,  1646, "South India",  80, 85, 84),
    ("Deccan Sultanates",         17.5,  78.5,  1500,  1687, "South Asia",   74, 72, 78),
    ("Mughal Empire",             28.6,  77.2,  1526,  1857, "South Asia",   90, 88, 90),
    ("Maratha Empire",            18.5,  73.8,  1674,  1818, "South Asia",   78, 75, 92),
    ("Sikh Empire",               31.6,  74.9,  1799,  1849, "South Asia",   78, 76, 88),
    ("Kingdom of Mysore",         12.3,  76.6,  1399,  1947, "South India",  76, 78, 80),
    ("Travancore Kingdom",         8.5,  76.9,  1729,  1949, "South India",  74, 80, 72),
    ("Hyderabad State",           17.4,  78.5,  1724,  1948, "South Asia",   78, 76, 74),
    ("Rajput Kingdoms",           26.9,  75.8,   700,  1200, "South Asia",   74, 76, 82),
    ("Gond Kingdom",              21.9,  80.0,  1300,  1750, "South Asia",   70, 68, 74),
    ("Kalinga Kingdom",           20.3,  85.8,  -300,   260, "South Asia",   76, 78, 80),
]


def _try_float(val: str, default: float = 50.0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _try_int(val: str, default: int = 0) -> int:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def load_civilizations(filepath: str) -> list[Civilization]:
    if not os.path.exists(filepath):
        print(f"WARNING: {filepath} not found - using built-in data ({len(BUILTIN)} civs)")
        return [Civilization(*row) for row in BUILTIN]

    civs: list[Civilization] = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rich = "resource_density" in headers

        for row in reader:
            try:
                if rich:
                    civs.append(Civilization(
                        name=row["name"],
                        lat=row["latitude"],
                        lon=row["longitude"],
                        start=row.get("start_year", 0),
                        end=row.get("end_year", 0),
                        region=row.get("region", "South Asia"),
                        resource=row.get("resource_density", 75),
                        knowledge=row.get("knowledge_density", 75),
                        military=row.get("military_strength", 75),
                    ))
                else:
                    # final_dataset.csv — enrich with BUILTIN scores by name match
                    name_col = "Civilization/Dynasty" if "Civilization/Dynasty" in headers else "name"
                    name = row[name_col]
                    match = next((b for b in BUILTIN if b[0].lower() in name.lower() or name.lower() in b[0].lower()), None)
                    civs.append(Civilization(
                        name=name,
                        lat=row["Latitude"],
                        lon=row["Longitude"],
                        start=row.get("Time (Approx Year)", 0),
                        end=match[4] if match else 0,
                        region=match[5] if match else "South Asia",
                        resource=match[6] if match else 75,
                        knowledge=match[7] if match else 75,
                        military=match[8] if match else 75,
                    ))
            except Exception as e:
                print(f"  Skipping row: {e}")

    # If CSV gave us fewer civs than BUILTIN, supplement with BUILTIN entries not already present
    names_loaded = {c.name.lower() for c in civs}
    for b in BUILTIN:
        if not any(b[0].lower() in n or n in b[0].lower() for n in names_loaded):
            civs.append(Civilization(*b))

    print(f"Loaded {len(civs)} civilizations from {os.path.basename(filepath)}")
    return civs
