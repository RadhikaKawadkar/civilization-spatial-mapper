import os
import hashlib
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# We only create the client if the URL and KEY are present.
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("WARNING: SUPABASE_URL or SUPABASE_KEY not found. Database operations will fail.")

def init_db():
    # No local initialization needed for Supabase. Tables must be created via SQL Editor.
    pass

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(name: str, email: str, password: str):
    if not supabase:
        return None
    try:
        data = {
            "name": name,
            "email": email,
            "password_hash": hash_password(password)
        }
        response = supabase.table("users").insert(data).execute()
        if len(response.data) > 0:
            return response.data[0]["id"]
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def get_user_by_email(email: str):
    if not supabase:
        return None
    response = supabase.table("users").select("*").eq("email", email).execute()
    if len(response.data) > 0:
        return response.data[0]
    return None

def get_user_by_id(user_id: int):
    if not supabase:
        return None
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    if len(response.data) > 0:
        return response.data[0]
    return None

def add_custom_civilization(name, lat, lon, region, resource, knowledge, military, added_by_id):
    if not supabase:
        return None
    try:
        data = {
            "name": name,
            "lat": lat,
            "lon": lon,
            "start_year": 0,
            "end_year": 0,
            "region": region,
            "resource_density": resource,
            "knowledge_density": knowledge,
            "military_strength": military,
            "added_by_id": added_by_id
        }
        response = supabase.table("custom_civilizations").insert(data).execute()
        if len(response.data) > 0:
            return response.data[0]["id"]
        return None
    except Exception as e:
        print(f"Error adding custom civilization: {e}")
        return None

def get_custom_civilizations():
    if not supabase:
        return []
    # Use users(name) for a LEFT JOIN (base data will have added_by_id=null)
    response = supabase.table("custom_civilizations").select("*, users(name)").execute()
    rows = []
    for item in response.data:
        # Reformat the result to match the expected format
        item["added_by_name"] = item.get("users", {}).get("name") if item.get("users") else None
        rows.append(item)
    return rows
