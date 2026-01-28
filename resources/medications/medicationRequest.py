import os
import sys
from tqdm import tqdm
from dotenv import load_dotenv
from fhirpy import SyncFHIRClient

load_dotenv()
SERVER_URL = os.getenv("SERVER_URL")

# List of standard MedicationRequest fields to check for
# Based on FHIR R4 Specification
EXPECTED_FIELDS = [
    'resourceType', 'id', 'identifier', 'status', 'statusReason',
    'intent', 'category', 'priority', 'doNotPerform', 
    'reportedBoolean', 'reportedReference', # reported[x]
    'medicationCodeableConcept', 'medicationReference', # medication[x]
    'subject', 'encounter', 'supportingInformation', 'authoredOn',
    'requester', 'performer', 'performerType', 'recorder',
    'reasonCode', 'reasonReference', 'instantiatesCanonical', 'instantiatesUri',
    'basedOn', 'groupIdentifier', 'courseOfTherapyType', 
    'insurance', 'note', 'dosageInstruction', 'dispenseRequest',
    'substitution', 'priorPrescription', 'detectedIssue', 'eventHistory'
]

def main():
    
    # 1. CLIENT INITIALIZATION
    try:
        client = SyncFHIRClient(SERVER_URL)
    except Exception as e:
        print(f"Error: Could not create client. {e}")
        sys.exit(1)

    # 2. FETCH DATA (MedicationRequest)
    print("Fetching MedicationRequests from server...")
    try:
        # Fetch all records
        # Note: We query 'MedicationRequest'
        med_requests = client.resources('MedicationRequest').sort('_lastUpdated').fetch_all()
    except Exception as e:
        print(f"Connection Error: {e}")
        sys.exit(1)

    if not med_requests:
        print("No MedicationRequest records found on the server.")
        sys.exit(1)

    total_records = len(med_requests)
    print(f"{total_records} MedicationRequests found. Analyzing field coverage...")

    # 3. ANALYZE FIELDS
    # Initialize set with expected fields so they always appear in report
    all_fields_found = set(EXPECTED_FIELDS)
    field_counts = {field: 0 for field in EXPECTED_FIELDS}

    # Iterate with loading bar
    for med in tqdm(med_requests, desc="Scanning Attributes"):
        
        # Serialize to dictionary to inspect actual JSON keys
        data = med.serialize() 
        
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
    print("\n--MedicationRequest Analysis--")
    
    # Sort fields alphabetically
    sorted_fields = sorted(list(all_fields_found))

    for field in sorted_fields:
        count = field_counts.get(field, 0)
        
        if count == 0:
            print(f"{field:<30} -> Not present")
        else:
            percentage = (count / total_records) * 100
            print(f"{field:<30} -> [{count}] - [{percentage:.1f}%]")

if __name__ == "__main__":
    main()