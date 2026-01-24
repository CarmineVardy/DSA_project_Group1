import requests
import sys
import os
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

FHIR_SERVER_URL = os.getenv("SERVER_URL")

# List of resources to process: [ResourceType, EstimatedCount, Description]
medical_resources = [
    ["Observation", 669898, ""],
    ["Claim", 353347, ""],
    ["MedicationRequest", 209401, ""],
    ["DiagnosticReport", 201152, ""],
    ["DocumentReference", 143946, ""],
    ["Encounter", 143946, ""],
    ["ExplanationOfBenefit", 143946, ""],
    ["Procedure", 56092, ""],
    ["Condition", 15956, ""],
    ["Immunization", 11900, ""],
    ["CarePlan", 6135, ""],
    ["CareTeam", 6135, ""],
    ["ImagingStudy", 3752, ""],
    ["Medication", 1350, ""],
    ["MedicationAdministration", 1350, ""],
    ["Patient", 1278, ""],
    ["Provenance", 1278, ""],
    ["Media", 1072, ""],
    ["Location", 1067, ""],
    ["Organization", 1067, ""],
    ["Practitioner", 1041, ""],
    ["PractitionerRole", 1041, ""],
    ["Device", 416, ""],
    ["AllergyIntolerance", 106, ""]
]

def extract_resource_info(entry):
    """
    Extracts the relevant display string from a FHIR resource entry 
    based on its resource type.
    """
    resource = entry.get('resource', {})
    resource_type = resource.get('resourceType')
    
    try:
        # --- Specific Logic based on Resource Type ---

        if resource_type == 'CarePlan':
            # Extract Category - Activity - Status
            # Note: Category text is often at index 1 in Synthea data
            categories = resource.get('category', [{}, {}])
            cat_text = categories[1].get('text') if len(categories) > 1 else categories[0].get('text')
            
            activity = resource.get('activity', [{}])[0]
            act_text = activity.get('detail', {}).get('code', {}).get('text')
            status = activity.get('detail', {}).get('status')
            return f"{cat_text} - {act_text} ({status})"

        elif resource_type == 'CareTeam':
            # Extract Doctor Name and Role (Participant index 1)
            participants = resource.get('participant', [])
            if len(participants) > 1:
                care_name = participants[1].get('member', {}).get('display')
                care_role = participants[1].get('role', [{}])[0].get('text')
                return f"{care_name} - {care_role}"
            return None

        elif resource_type == 'ImagingStudy':
            # Extract Modality: Title - BodySite
            series = resource.get('series', [{}])[0]
            modality = series.get('modality', {}).get('display')
            title = series.get('instance', [{}])[0].get('title')
            body_site = series.get('bodySite', {}).get('display')
            return f"{modality}: {title} - {body_site}"

        elif resource_type == 'Encounter':
            # Extract Type (Status)
            type_display = resource.get('type', [{}])[0].get('coding', [{}])[0].get('display')
            status = resource.get('status')
            return f"{type_display} ({status})"

        elif resource_type == 'Immunization':
            # Extract Vaccine Display
            return resource.get('vaccineCode', {}).get('coding', [{}])[0].get('display')

        elif resource_type == 'Patient':
            # Extract Gender
            return resource.get('gender')

        elif resource_type == 'Media':
            # Extract Reason Code
            return resource.get('reasonCode', [{}])[0].get('coding', [{}])[0].get('display')

        elif resource_type == 'Location':
            # Extract Name - City (State) Zip
            name = resource.get('name')
            addr = resource.get('address', {})
            return f"{name} - {addr.get('city')} ({addr.get('state')}) {addr.get('postalCode')}"

        elif resource_type == 'Organization':
            # Extract Name - City (State) Zip (Address is a list here)
            name = resource.get('name')
            addr_list = resource.get('address', [{}])
            addr = addr_list[0] if addr_list else {}
            return f"{name} - {addr.get('city')} ({addr.get('state')}) {addr.get('postalCode')}"

        elif resource_type == 'PractitionerRole':
            # Extract Practitioner - Specialty - Organization
            prac_name = resource.get('practitioner', {}).get('display')
            specialty = resource.get('code', [{}])[0].get('coding', [{}])[0].get('display')
            org_name = resource.get('organization', {}).get('display')
            return f"{prac_name} - {specialty} - {org_name}"

        elif resource_type == 'MedicationAdministration':
            # Extract Medication Display - Status
            med_display = resource.get('medicationCodeableConcept', {}).get('coding', [{}])[0].get('display')
            status = resource.get('status')
            return f"{med_display} - {status}"
            # Retrieving only the specimen
            # return resource.get('medicationCodeableConcept', {}).get('coding', [{}])[0].get('display')

        elif resource_type == 'MedicationRequest':
            # Extract Medication Display
            return resource.get('medicationCodeableConcept', {}).get('coding', [{}])[0].get('display')
        
        elif resource_type == 'ExplanationOfBenefit':
            # Extract Product Or Service Display
            items = resource.get('item', [])
            if items:
                prod = items[0].get('productOrService', {})
                # Try coding display first
                codings = prod.get('coding', [])
                if codings and codings[0].get('display'):
                    return codings[0].get('display')
                elif prod.get('text'):
                    # Fallback to text
                    return prod.get('text')
            return None
        
        elif resource_type == 'Claim':
            # Extract Item Display - Total Value Currency
            # 1. Get Item Display (General examination of patient)
            items = resource.get('item', [])
            item_display = "Unknown Item"
            if items:
                prod = items[0].get('productOrService', {})
                # Try coding display first
                codings = prod.get('coding', [])
                if codings and codings[0].get('display'):
                    item_display = codings[0].get('display')
                elif prod.get('text'):
                    # Fallback to text if coding display is missing
                    item_display = prod.get('text')
            
            # 2. Get Total Value and Currency
            total_obj = resource.get('total', {})
            value = total_obj.get('value', '0')
            currency = total_obj.get('currency', '')
            
            return f"{item_display}"

        # --- Generic Fallbacks for other types (Observation, Condition, etc.) ---
        
        # Check for 'code' field (common in Observation, Condition, Procedure, Device)
        code_payload = resource.get('code', {})
        if 'coding' in code_payload and len(code_payload['coding']) > 0:
            return code_payload['coding'][0].get('display')
        elif 'text' in code_payload:
            return code_payload['text']
        
        # Check for 'type' field (common in DocumentReference, Claim fallback)
        type_payload = resource.get('type', {})
        if isinstance(type_payload, dict) and 'coding' in type_payload:
             return type_payload['coding'][0].get('display')
             
        # Check for 'item' field
        items = resource.get('item', [])
        if items:
            return items[0].get('productOrService', {}).get('text')

    except Exception:
        # Return None if any path fails, allowing the loop to skip this entry
        return None

    return None

def get_unique_types(base_url, resource_type, total_count):
    """
    Downloads all resources of a specific type and returns a set of unique 
    formatted strings based on the extraction logic.
    """
    
    # Initialize query with a high count per page to reduce HTTP requests
    query_url = f"{base_url}/{resource_type}?_count=500"
    unique_types = set()
    
    print(f"Connecting to: {base_url}")
    print(f"Scanning approximately {total_count} {resource_type}s...")

    with tqdm(total=total_count, unit="res", desc=f"Processing {resource_type}") as pbar:
        while query_url:
            try:
                response = requests.get(query_url)
                response.raise_for_status()
                bundle = response.json()
            except requests.exceptions.ConnectionError:
                print(f"\n[ERROR] Connection failed connecting to {base_url}.")
                sys.exit(1)
            except Exception as e:
                print(f"\n[ERROR] Generic error: {e}")
                sys.exit(1)

            entries = bundle.get('entry', [])

            if entries:
                for entry in entries:
                    # Use the helper function to extract data
                    info = extract_resource_info(entry)
                    if info:
                        unique_types.add(info)
                
                # Update progress bar
                pbar.update(len(entries))
                pbar.set_postfix(Unique=len(unique_types))

            # Handle Pagination: Look for the 'next' link
            query_url = None
            for link in bundle.get('link', []):
                if link['relation'] == 'next':
                    query_url = link['url']
                    break
    
    return unique_types

if __name__ == "__main__":
    
    if not FHIR_SERVER_URL:
        print("ERROR: SERVER_URL not found in environment variables.")
        sys.exit(1)

    # Define the output directory
    directory_name = "info_unique_resources"

    # Create the directory if it does not exist
    try:
        os.makedirs(directory_name, exist_ok=True)
        print(f"Output directory checked/created: '{directory_name}'\n")
    except Exception as e:
        print(f"Error creating directory: {e}")
        sys.exit(1)

    try:
        for res_type, estimated_count, _ in medical_resources:
            
            # 1. Fetch unique types for the current resource
            types_found = get_unique_types(FHIR_SERVER_URL, res_type, estimated_count)
            
            # 2. Sort results
            sorted_types = sorted(types_found)
            
            # 3. Define filename
            filename = f"{directory_name}/{res_type}_results.txt"
            
            # 4. Write results to file
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"Report generated for: {res_type}\n")
                    f.write(f"Server: {FHIR_SERVER_URL}\n")
                    f.write(f"Total Unique Values Found: {len(types_found)}\n")
                    f.write("=" * 50 + "\n")
                    
                    if not sorted_types:
                        f.write("No unique values found or extraction failed.\n")
                    else:
                        for t in sorted_types:
                            f.write(f"{t}\n")
                            
                print(f"Saved {len(sorted_types)} unique items to {filename}")
                print("-" * 50 + "\n")
                
            except Exception as e:
                print(f"Error writing to file {filename}: {e}")

    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(0)
