import os
import sys

from dotenv import load_dotenv
from fhirpy import SyncFHIRClient

load_dotenv()
SERVER_URL = os.getenv("SERVER_URL")

def main():
   
    # CLIENT INITIALIZATION
    try:
        client = SyncFHIRClient(SERVER_URL)
    except Exception as e:
        print(f"Error: Could not create client. {e}")
        sys.exit(1)

    # FETCH DATA (all patients)
    try:
        patients = client.resources('Patient') \
            .sort('_lastUpdated') \
            .elements('id', 'name') \
            .fetch_all()        
    except Exception as e:
        print(f"Connection Error: {e}")
        sys.exit(1)

    if not patients:
        print("No patients found on the server.")
        sys.exit(1)

    print(f"{len(patients)} patients.")

    # BUILD MAP (ID -> Name) 
    patients_map = {}
    
    for patient in patients:
        # --- Parsing Logic (Inline) ---
        p_id = patient.id
        full_name = "Unknown"
        # Check if 'name' attribute exists (fhirpy objects allow dot notation)
        if patient.get('name'):
            # Name is a list, take the first one
            name_entry = patient.name[0]
            # Extract Family (String)
            family = name_entry.get('family', '')
            # Extract Given (List of Strings) -> Join them
            given_list = name_entry.get('given', [])
            given = " ".join(given_list)
            full_name = f"{given} {family}".strip()
        # Add to map
        patients_map[p_id] = full_name

    # PRINT THE MAP 
    print("\n--- PATIENT LIST ---")
    print(f"{'INDEX':<5} | {'ID':<40} | {'NAME'}")
    print("-" * 70)

    # Convert map to list to allow indexing (0, 1, 2...)
    # patient_list becomes: [ (id1, name1), (id2, name2), ... ]
    patient_list = list(patients_map.items())

    for i, (pid, pname) in enumerate(patient_list):
        print(f"[{i}]   | {pid:<40} | {pname}")

    print("-" * 70)

if __name__ == "__main__":
    main()