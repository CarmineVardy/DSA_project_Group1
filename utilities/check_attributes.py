import os
import sys
from tqdm import tqdm
from dotenv import load_dotenv
from fhirpy import SyncFHIRClient

load_dotenv()
SERVER_URL = os.getenv("SERVER_URL")

# List of standard Procedure fields to check for
# Based on FHIR R4 Specification
EXPECTED_FIELDS = [
    'resourceType', 'id', 'identifier', 'instantiatesCanonical', 
    'instantiatesUri', 'basedOn', 'partOf', 'status', 'statusReason', 
    'category', 'code', 'subject', 'encounter', 
    # performed[x] polymorphic fields:
    'performedDateTime', 'performedPeriod', 'performedString', 
    'performedAge', 'performedRange', 
    'recorder', 'asserter', 'performer', 'location', 'reasonCode', 
    'reasonReference', 'bodySite', 'outcome', 'report', 'complication', 
    'complicationDetail', 'followUp', 'note', 'focalDevice', 
    'usedReference', 'usedCode'
]

def main():
    
    # 1. CLIENT INITIALIZATION
    try:
        client = SyncFHIRClient(SERVER_URL)
    except Exception as e:
        print(f"Error: Could not create client. {e}")
        sys.exit(1)

    # 2. FETCH DATA (Procedure)
    print("Fetching Procedures from server...")
    try:
        # Fetch all records
        # Note: We query 'Procedure' 
        procedures = client.resources('Procedure').sort('_lastUpdated').fetch_all()
    except Exception as e:
        print(f"Connection Error: {e}")
        sys.exit(1)

    if not procedures:
        print("No Procedure records found on the server.")
        sys.exit(1)

    total_records = len(procedures)
    print(f"{total_records} Procedures found. Analyzing field coverage...")

    # 3. ANALYZE FIELDS
    # Initialize set with expected fields so they always appear in report
    all_fields_found = set(EXPECTED_FIELDS)
    field_counts = {field: 0 for field in EXPECTED_FIELDS}

    # Iterate with loading bar
    for proc in tqdm(procedures, desc="Scanning Attributes"):
        
        # Serialize to dictionary to inspect actual JSON keys
        data = proc.serialize() 
        
        for key, value in data.items():
            # Check if value exists (not None)
            if value is not None:
                # Add to set (catches any custom/unexpected fields)
                all_fields_found.add(key)
                
                # Increment counter
                if key in field_counts:
                    field_counts[key] += 1
                else:
                    field_counts[key] = 1

    # 4. PRINT REPORT
    print("\n--Procedure Analysis--")
    
    # Sort fields alphabetically
    sorted_fields = sorted(list(all_fields_found))

    for field in sorted_fields:
        count = field_counts.get(field, 0)
        
        if count == 0:
            print(f"{field:<25} -> Not present")
        else:
            percentage = (count / total_records) * 100
            print(f"{field:<25} -> [{count}] - [{percentage:.1f}%]")

if __name__ == "__main__":
    main()