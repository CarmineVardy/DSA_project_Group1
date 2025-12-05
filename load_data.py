import os
from dotenv import load_dotenv
load_dotenv()

import json
import requests
import sys

DATASET_PATH = os.getenv("DATASET_PATH")
SERVER_URL = os.getenv("SERVER_URL")

def upload_fhir_bundles():
    # Construct the full path to the 'fhir' subdirectory inside the dataset path
    fhir_folder_path = os.path.join(DATASET_PATH, "fhir")

    # Validate that the 'fhir' folder exists
    if not os.path.exists(fhir_folder_path):
        print(f"ERROR: The folder '{fhir_folder_path}' does not exist.")
        print(f"Please check that DATASET_PATH is correct and contains a 'fhir' subfolder.")
        sys.exit(1)

    # Standard headers for FHIR JSON content
    headers = {
        'Content-Type': 'application/fhir+json',
        'Accept': 'application/fhir+json'
    }

    print(f"--- Starting upload to: {SERVER_URL} ---")
    print(f"--- Source folder: {fhir_folder_path} ---\n")

    files_processed = 0
    files_success = 0
    files_error = 0

    # ------------------------------------------------------------------
    # SORTING LOGIC: Priority to lowercase files (Infrastructure)
    # ------------------------------------------------------------------
    all_files = [f for f in os.listdir(fhir_folder_path) if f.endswith(".json")]
    
    # Separate files into two lists:
    # 1. Infrastructure files (start with lowercase letter, e.g., practitioner.json)
    # 2. Patient files (start with Uppercase letter/Number, e.g., Aaron697.json)
    infrastructure_files = []
    patient_files = []

    for f in all_files:
        if f[0].islower():
            infrastructure_files.append(f)
        else:
            patient_files.append(f)

    # Sort them alphabetically within their groups for consistency
    infrastructure_files.sort()
    patient_files.sort()

    # Create the final ordered list: Infrastructure FIRST, Patients SECOND
    ordered_file_list = infrastructure_files + patient_files

    print(f"Found {len(ordered_file_list)} JSON files.")
    print(f" - Infrastructure files (High Priority): {len(infrastructure_files)}")
    print(f" - Patient/Data files: {len(patient_files)}")
    print("-" * 50 + "\n")

    # ------------------------------------------------------------------
    # UPLOAD LOOP
    # ------------------------------------------------------------------
    for filename in ordered_file_list:
        file_path = os.path.join(fhir_folder_path, filename)
        files_processed += 1
        
        print(f"[{files_processed}/{len(ordered_file_list)}] Processing file: {filename}...")

        try:
            # 1. Read the JSON file content
            with open(file_path, 'r', encoding='utf-8') as f:
                bundle_data = json.load(f)

            # 2. Preliminary Validation
            # We verify if the file is indeed a Bundle of type 'transaction'
            resource_type = bundle_data.get('resourceType', '')
            bundle_type = bundle_data.get('type', '')

            if resource_type != 'Bundle' or bundle_type != 'transaction':
                print(f"  [SKIP] File is not a 'transaction' type Bundle. "
                      f"(Found Resource: {resource_type}, Type: {bundle_type})")
                continue

            # 3. Send POST request to the FHIR Server
            response = requests.post(
                url=SERVER_URL,
                json=bundle_data,
                headers=headers
            )

            # 4. Check the response status
            if response.status_code == 200:
                print(f"  [OK] Success! Server response: 200 OK")
                files_success += 1
            else:
                # Print error details if the upload failed
                print(f"  [ERROR] Status Code: {response.status_code}")
                # Print the first 200 characters of the error message for debugging
                print(f"  [DETAIL] {response.text[:200]}...") 
                files_error += 1

        except json.JSONDecodeError:
            print(f"  [ERROR] The file contains invalid JSON.")
            files_error += 1
        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] Connection error: {e}")
            files_error += 1
        except Exception as e:
            print(f"  [ERROR] Generic error: {e}")
            files_error += 1
        
        # Separator line for readability
        print("-" * 30)

    # Final Summary
    print("\n=== UPLOAD SUMMARY ===")
    print(f"Total files processed: {files_processed}")
    print(f"Successfully uploaded: {files_success}")
    print(f"Errors encountered: {files_error}")

if __name__ == "__main__":
    upload_fhir_bundles()