import os
import hashlib
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

# ── PostgreSQL connection ─────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")

def get_connection():
    """Open and return a new psycopg2 connection."""
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Add it to backend/.env as a PostgreSQL connection string.\n"
            "  Example: DATABASE_URL=postgresql://user:password@localhost:5432/civilization_mapper"
        )
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# ── Full civilization dataset ─────────────────────────────────────
# 47 Indian civilizations + global civilizations
SEED_CIVILIZATIONS = [
    # === INDIAN / SOUTH ASIAN CIVILIZATIONS ===
    ("Indus Valley (Harappan)",      25.0,   67.0,  -2600, -1900, "South Asia",    88, 85, 60),
    ("Early Harappan",               28.0,   70.0,  -3300, -2600, "South Asia",    82, 80, 55),
    ("Late Harappan",                27.0,   68.0,  -1900, -1300, "South Asia",    78, 75, 52),
    ("Vedic Civilization",           28.5,   77.0,  -1500,  -600, "South Asia",    75, 92, 70),
    ("Painted Grey Ware Culture",    29.0,   77.5,  -1200,  -600, "South Asia",    70, 72, 60),
    ("Mahajanapadas",                25.0,   85.0,   -600,  -321, "South Asia",    78, 85, 75),
    ("Magadha",                      25.2,   86.0,   -600,  -321, "South Asia",    80, 88, 82),
    ("Maurya Empire",                25.6,   85.1,   -322,  -185, "South Asia",    85, 88, 85),
    ("Shunga Dynasty",               25.0,   82.0,   -185,   -73, "South Asia",    72, 78, 70),
    ("Kanva Dynasty",                25.0,   82.0,    -73,    28, "South Asia",    68, 74, 65),
    ("Satavahana Dynasty",           19.0,   78.0,   -100,   220, "South Asia",    80, 82, 78),
    ("Indo-Greek Kingdom",           34.0,   72.0,   -180,    10, "South Asia",    75, 80, 78),
    ("Kushan Empire",                34.5,   71.0,     50,   375, "Central Asia",  82, 80, 85),
    ("Western Kshatrapas",           22.5,   72.0,     35,   415, "South Asia",    70, 72, 72),
    ("Gupta Empire",                 23.0,   77.0,    320,   550, "South Asia",    85, 95, 78),
    ("Vakataka Dynasty",             20.5,   79.0,    250,   500, "South Asia",    74, 80, 72),
    ("Maitraka Dynasty",             22.3,   72.6,    475,   767, "South Asia",    72, 75, 70),
    ("Chalukya Dynasty",             15.5,   75.0,    543,   753, "South India",   78, 82, 80),
    ("Rashtrakuta Dynasty",          16.0,   75.5,    753,   982, "South India",   79, 84, 83),
    ("Pallava Dynasty",              12.8,   80.2,    275,   897, "South India",   78, 87, 80),
    ("Chola Dynasty",                10.8,   79.1,    300,  1279, "South India",   82, 88, 86),
    ("Pandya Dynasty",                9.9,   78.1,    300,  1345, "South India",   76, 82, 74),
    ("Chera Dynasty",                10.3,   76.3,    300,  1102, "South India",   80, 82, 72),
    ("Hoysala Empire",               13.0,   76.1,   1026,  1343, "South India",   78, 85, 76),
    ("Kakatiya Dynasty",             18.0,   79.6,   1083,  1323, "South India",   76, 80, 78),
    ("Seuna (Yadava) Dynasty",       19.9,   73.8,    850,  1334, "South Asia",    74, 78, 76),
    ("Paramara Dynasty",             23.5,   75.8,    800,  1305, "South Asia",    72, 76, 74),
    ("Chandela Dynasty",             24.8,   79.9,    831,  1315, "South Asia",    74, 80, 76),
    ("Gurjara-Pratihara",            27.0,   73.0,    730,  1036, "South Asia",    76, 78, 80),
    ("Pala Empire",                  24.0,   88.0,    750,  1161, "South Asia",    77, 90, 76),
    ("Sena Dynasty",                 23.0,   89.0,   1097,  1230, "South Asia",    72, 80, 72),
    ("Ahom Kingdom",                 26.5,   92.7,   1228,  1826, "South Asia",    74, 76, 82),
    ("Kamarupa Kingdom",             26.0,   91.8,    350,  1140, "South Asia",    72, 74, 70),
    ("Kashmir Shaiva Kingdoms",      34.1,   74.8,    800,  1339, "South Asia",    70, 88, 68),
    ("Delhi Sultanate",              28.6,   77.2,   1206,  1526, "South Asia",    76, 72, 88),
    ("Bahmani Sultanate",            17.0,   76.8,   1347,  1527, "South Asia",    74, 74, 80),
    ("Vijayanagara Empire",          15.3,   76.5,   1336,  1646, "South India",   80, 85, 84),
    ("Deccan Sultanates",            17.5,   78.5,   1500,  1687, "South Asia",    74, 72, 78),
    ("Mughal Empire",                28.6,   77.2,   1526,  1857, "South Asia",    90, 88, 90),
    ("Maratha Empire",               18.5,   73.8,   1674,  1818, "South Asia",    78, 75, 92),
    ("Sikh Empire",                  31.6,   74.9,   1799,  1849, "South Asia",    78, 76, 88),
    ("Kingdom of Mysore",            12.3,   76.6,   1399,  1947, "South India",   76, 78, 80),
    ("Travancore Kingdom",            8.5,   76.9,   1729,  1949, "South India",   74, 80, 72),
    ("Hyderabad State",              17.4,   78.5,   1724,  1948, "South Asia",    78, 76, 74),
    ("Rajput Kingdoms",              26.9,   75.8,    700,  1200, "South Asia",    74, 76, 82),
    ("Gond Kingdom",                 21.9,   80.0,   1300,  1750, "South Asia",    70, 68, 74),
    ("Kalinga Kingdom",              20.3,   85.8,   -300,   260, "South Asia",    76, 78, 80),
    # === GLOBAL CIVILIZATIONS ===
    ("Ancient Egypt",                26.8,   30.8,  -3100,  -332, "North Africa",  80, 78, 81),
    ("Mesopotamia",                  33.0,   44.4,  -3500,  -539, "Middle East",   78, 80, 75),
    ("Ancient Greece",               37.9,   23.7,   -800,  -146, "Mediterranean", 70, 95, 72),
    ("Roman Empire",                 41.9,   12.5,    -27,   476, "Mediterranean", 80, 70, 88),
    ("Han China",                    35.0,  105.0,   -206,   220, "East Asia",     88, 90, 85),
    ("Maya",                         16.0,  -89.0,    250,   900, "Mesoamerica",   70, 88, 65),
    ("Persian Empire",               32.0,   53.0,   -550,  -330, "Middle East",   85, 75, 90),
    ("Byzantine",                    41.0,   29.0,    330,  1453, "Mediterranean", 75, 80, 78),
    ("Aztec",                        19.4,  -99.1,   1300,  1521, "Mesoamerica",   72, 80, 85),
    ("Mongol Empire",                47.0,  106.0,   1206,  1368, "Central Asia",  65, 60, 98),
    ("Ottoman Empire",               39.9,   32.9,   1299,  1922, "Middle East",   80, 72, 88),
    ("Inca",                        -13.5,  -72.0,   1400,  1533, "South America", 78, 75, 82),
]


def init_db():
    """
    Create tables if they do not already exist and seed civilizations.
    Safe to call every startup — uses IF NOT EXISTS / ON CONFLICT DO NOTHING.
    """
    ddl = """
    CREATE TABLE IF NOT EXISTS users (
        id              BIGSERIAL PRIMARY KEY,
        name            TEXT NOT NULL,
        email           TEXT UNIQUE NOT NULL,
        password_hash   TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS civilizations (
        id                  BIGSERIAL PRIMARY KEY,
        name                TEXT UNIQUE NOT NULL,
        latitude            DOUBLE PRECISION NOT NULL,
        longitude           DOUBLE PRECISION NOT NULL,
        start_year          INTEGER DEFAULT 0,
        end_year            INTEGER DEFAULT 0,
        region              TEXT DEFAULT 'Unknown',
        resource_density    DOUBLE PRECISION DEFAULT 50.0,
        knowledge_density   DOUBLE PRECISION DEFAULT 50.0,
        military_strength   DOUBLE PRECISION DEFAULT 50.0
    );

    CREATE TABLE IF NOT EXISTS custom_civilizations (
        id                  BIGSERIAL PRIMARY KEY,
        name                TEXT UNIQUE NOT NULL,
        lat                 DOUBLE PRECISION NOT NULL,
        lon                 DOUBLE PRECISION NOT NULL,
        start_year          INTEGER,
        end_year            INTEGER,
        region              TEXT,
        resource_density    DOUBLE PRECISION,
        knowledge_density   DOUBLE PRECISION,
        military_strength   DOUBLE PRECISION,
        added_by_id         BIGINT REFERENCES users(id)
    );
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
        print("[DB] Tables verified / created.")
        _seed_civilizations(conn)
    finally:
        conn.close()


def _seed_civilizations(conn=None):
    """Insert all built-in civilizations, skipping duplicates."""
    sql = """
        INSERT INTO civilizations
            (name, latitude, longitude, start_year, end_year, region,
             resource_density, knowledge_density, military_strength)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (name) DO NOTHING;
    """
    close_after = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                for row in SEED_CIVILIZATIONS:
                    cur.execute(sql, row)
        print(f"[DB] Seeded / verified {len(SEED_CIVILIZATIONS)} civilizations.")
    finally:
        if close_after:
            conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── User operations ───────────────────────────────────────────────

def create_user(name: str, email: str, password: str):
    """Insert a new user. Returns the new user ID, or None on failure."""
    sql = """
        INSERT INTO users (name, email, password_hash)
        VALUES (%s, %s, %s)
        RETURNING id;
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (name, email, hash_password(password)))
                row = cur.fetchone()
                return row["id"] if row else None
    except psycopg2.errors.UniqueViolation:
        # email already exists
        return None
    except Exception as e:
        print(f"[DB] Error creating user: {e}")
        return None
    finally:
        conn.close()


def get_user_by_email(email: str):
    """Return the user row dict for a given email, or None."""
    sql = "SELECT * FROM users WHERE email = %s LIMIT 1;"
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (email,))
            return cur.fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id: int):
    """Return the user row dict for a given ID, or None."""
    sql = "SELECT * FROM users WHERE id = %s LIMIT 1;"
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            return cur.fetchone()
    finally:
        conn.close()


def update_user_password(user_id: int, new_password: str) -> bool:
    """Update the password hash for a user. Returns True on success."""
    sql = "UPDATE users SET password_hash = %s WHERE id = %s;"
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (hash_password(new_password), user_id))
                return cur.rowcount > 0
    except Exception as e:
        print(f"[DB] Error updating password: {e}")
        return False
    finally:
        conn.close()


# ── Main civilization operations ─────────────────────────────────

def get_all_civilizations():
    """Return all built-in civilizations from the database."""
    sql = """
        SELECT id, name, latitude, longitude, start_year, end_year,
               region, resource_density, knowledge_density, military_strength
        FROM civilizations
        ORDER BY id;
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Custom civilization operations ───────────────────────────────

def add_custom_civilization(name, lat, lon, region, resource, knowledge, military, added_by_id):
    """Insert a custom civilization. Returns the new row ID, or None on failure."""
    sql = """
        INSERT INTO custom_civilizations
            (name, lat, lon, start_year, end_year, region,
             resource_density, knowledge_density, military_strength, added_by_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    name, lat, lon, 0, 0, region,
                    resource, knowledge, military, added_by_id
                ))
                row = cur.fetchone()
                return row["id"] if row else None
    except psycopg2.errors.UniqueViolation:
        # name already exists
        return None
    except Exception as e:
        print(f"[DB] Error adding civilization: {e}")
        return None
    finally:
        conn.close()


def get_custom_civilizations():
    """Return all custom civilizations with the adder's name joined in."""
    sql = """
        SELECT
            cc.*,
            u.name AS added_by_name
        FROM custom_civilizations cc
        LEFT JOIN users u ON u.id = cc.added_by_id
        ORDER BY cc.id;
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            # psycopg2.extras.RealDictCursor returns dict-like rows; convert to plain dicts
            return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_custom_civilization(name: str, user_id: int) -> bool:
    """
    Delete a custom civilization by name, only if it was added by user_id.
    Returns True if a row was deleted, False otherwise.
    """
    sql = """
        DELETE FROM custom_civilizations
        WHERE name = %s AND added_by_id = %s;
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (name, user_id))
                return cur.rowcount > 0
    except Exception as e:
        print(f"[DB] Error deleting civilization: {e}")
        return False
    finally:
        conn.close()


def delete_builtin_civilization(name: str) -> bool:
    """
    Delete a built-in civilization by name.
    Returns True if a row was deleted, False otherwise.
    """
    sql = "DELETE FROM civilizations WHERE name = %s;"
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (name,))
                return cur.rowcount > 0
    except Exception as e:
        print(f"[DB] Error deleting built-in civilization: {e}")
        return False
    finally:
        conn.close()


def get_civilizations_by_user(user_id: int):
    """Return all custom civilizations added by a specific user."""
    sql = """
        SELECT
            cc.*,
            u.name AS added_by_name
        FROM custom_civilizations cc
        LEFT JOIN users u ON u.id = cc.added_by_id
        WHERE cc.added_by_id = %s
        ORDER BY cc.id;
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
