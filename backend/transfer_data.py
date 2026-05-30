import os
from dotenv import load_dotenv
from supabase import create_client, Client
from loader import load_civilizations

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in environment variables.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def transfer_data():
    csv_path = "../civilizations.csv" if os.path.exists("../civilizations.csv") else "../data/final_dataset.csv"
    civs = load_civilizations(csv_path)
    print(f"Loaded {len(civs)} civilizations from local storage.")
    
    # We use custom_civilizations table for all civilizations
    # Clear existing data just in case, but supabase python client doesn't support truncate directly without filters
    # Let's just insert
    success_count = 0
    for civ in civs:
        data = {
            "name": civ.name,
            "lat": civ.latitude,
            "lon": civ.longitude,
            "start_year": civ.start_year,
            "end_year": civ.end_year,
            "region": civ.region,
            "resource_density": civ.resource_density,
            "knowledge_density": civ.knowledge_density,
            "military_strength": civ.military_strength,
            "added_by_id": None  # Base data has no associated user
        }
        
        try:
            res = supabase.table("custom_civilizations").insert(data).execute()
            if len(res.data) > 0:
                success_count += 1
        except Exception as e:
            print(f"Skipped {civ.name}: {e} (might already exist)")
            
    print(f"Successfully inserted {success_count} civilizations into Supabase.")

if __name__ == "__main__":
    transfer_data()
