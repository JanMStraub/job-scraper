import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

print(f"Testing connection to: {url}")
try:
    supabase: Client = create_client(url, key)
    # Try a simple query
    response = supabase.table("jobs").select("count", count="exact").limit(1).execute()
    print("Connection successful!")
    print(f"Response: {response}")
except Exception as e:
    print(f"Connection failed: {e}")
