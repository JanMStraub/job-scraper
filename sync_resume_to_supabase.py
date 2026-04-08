
import json
import supabase_utils
import logging

logging.basicConfig(level=logging.INFO)

def sync_resume():
    print("Reading local resume.json...")
    try:
        with open('resume.json', 'r', encoding='utf-8') as f:
            resume_data = json.load(f)
        
        print("Uploading resume to Supabase...")
        success = supabase_utils.save_base_resume(resume_data)
        
        if success:
            print("Successfully synced local resume.json to Supabase.")
        else:
            print("Failed to sync resume to Supabase.")
    except Exception as e:
        print(f"Error during sync: {e}")

if __name__ == "__main__":
    sync_resume()
