import os
import sys

from dotenv import load_dotenv
from fhirpy import SyncFHIRClient

from patient import AppPatient
from clinical_resources import AppCondition


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
    #For simplification and speed, we only load the first patient
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
            app_patient = AppPatient(patient.serialize())
            app_patients.append(app_patient)
        except Exception as e:
            p_id = patient.id if hasattr(patient, 'id') else "Unknown"
            print(f"[WARNING] Could not parse patient {p_id}: {e}")


    #IN THIS STEP WE HAVE TO IMPLEMENT THAT FOR EACH OBJECT AppPatient THE USER CAN SEE SOME INFORMATION (NAME, AGE)...AND CHOOSE ONE OF THEM

    # SIMULATION: User selects the first patient (or specific ID 5216)
    # We find the object in our list that matches ID '5216'
    target_id = "5216"
    selected_patient = next((p for p in app_patients if p.id == target_id), None)

    print(f"Choosen Patient with id: {selected_patient.id}.")


    if not selected_patient:
        print(f"Error: Patient {target_id} not found in local objects.")
        sys.exit(1)


    #START FROM CLINICAL RESOURCES
    ''' 
    AllergyIntolerance
    Condition (Problem)
    Procedure
    FamilyMemberHistory
    AdverseEvent
    CarePlan
    Goal
    CareTeam
    ClinicalImpression
    DetectedIssue
    ServiceRequest
    VisionPrescription
    RiskAssessment
    NutritionIntake
    NutritionOrder
    '''


    # we start from selected_patient

    # CONDITION
    conditions = []
    try:
        conditions = client.resources('Condition') \
            .search(patient=selected_patient.id) \
            .fetch()
    except Exception as e:
        print(f"[ERROR] Error fetching conditions for patient {selected_patient.id}: {e}")

    app_conditions = []
    for condition in conditions:
        try:
            app_cond = AppCondition(condition.serialize())
            app_conditions.append(app_cond)
        except Exception as e:
            c_id = condition.id if hasattr(condition, 'id') else "Unknown"
            print(f"[WARNING] Could not parse condition {c_id} for patient {selected_patient.id}: {e}")

    selected_patient.add_conditions(app_conditions)
    print(f"Update: Added {len(app_conditions)} conditions to Patient {selected_patient.id}.")




if __name__ == "__main__":
    main()