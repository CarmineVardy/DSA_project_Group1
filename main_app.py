import os
import sys

from dotenv import load_dotenv
from fhirpy import SyncFHIRClient

from patient import AppPatient

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
            .limit(1) \
            .fetch()
            #.fetch_all()                
    except Exception as e:
        print(f"Connection Error: {e}")
        sys.exit(1)

    # CHECK IF THERE ARE NO PATIENTS IN SERVER
    if not patients:
        print("No patients found on the server.")
        sys.exit(1)

    app_patients = []
    for patient in patients:
        try:
            patient_obj = AppPatient(patient.serialize())
            app_patients.append(patient_obj)
        except Exception as e:
            p_id = patient.id if hasattr(patient, 'id') else "Unknown"
            print(f"[WARNING] Could not parse patient {p_id}: {e}")

    for app_patient in app_patients:
        print(app_patient.get_full_name())
        print(app_patient.gender)
        print(app_patient.birthDate)
        print(app_patient.age)
        print(app_patient.isDeceased)
        print(app_patient.deceasedDate)


if __name__ == "__main__":
    main()