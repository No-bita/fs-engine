import os
import json
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
# The path to the downloaded service account key
CREDENTIAL_PATH = Path("/Users/aaryanshah/Downloads/FS Engine/FS Engine Firebase Admin SDK.json")

if not CREDENTIAL_PATH.exists():
    print(f"Error: Could not find credential file at {CREDENTIAL_PATH}")
    exit(1)

cred = credentials.Certificate(str(CREDENTIAL_PATH))
firebase_admin.initialize_app(cred)

db = firestore.client()

def migrate_data():
    json_dir = Path("/Users/aaryanshah/Downloads/FS Engine/data/json")
    if not json_dir.exists():
        print(f"Error: Data directory {json_dir} not found.")
        return

    count = 0
    for file in json_dir.glob("*.json"):
        if file.name.startswith("_"):
            continue
            
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Use the scheme ID as the document ID in Firestore
            scheme_id = data.get("scheme", {}).get("id")
            if not scheme_id:
                print(f"Skipping {file.name}: No scheme ID found.")
                continue
                
            # Upload to Firestore
            doc_ref = db.collection("schemes").document(scheme_id)
            doc_ref.set(data)
            print(f"Successfully migrated: {scheme_id}")
            count += 1
            
        except Exception as e:
            print(f"Error processing {file.name}: {e}")
            
    print(f"Migration complete. {count} schemes uploaded to Firestore.")

if __name__ == "__main__":
    migrate_data()
