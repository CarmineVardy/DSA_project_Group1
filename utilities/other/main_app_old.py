import os
import sys

from dotenv import load_dotenv
from fhirpy import SyncFHIRClient
from collections import defaultdict

from resources.administration.device import AppDevice
from resources.administration.patient import AppPatient
from resources.clinical.allergyIntolerance import AppAllergyIntolerance
from resources.clinical.carePlan import AppCarePlan
from resources.clinical.condition import AppCondition
from resources.clinical.procedure import AppProcedure
from resources.diagnostics.diagnosticReport import AppDiagnosticReport
from resources.diagnostics.documentReference import AppDocumentReference
from resources.diagnostics.observation import AppObservation
from resources.medications.immunization import AppImmunization
from resources.medications.medication import AppMedication
from resources.medications.medicationRequests import AppMedicationRequest


load_dotenv()
SERVER_URL = os.getenv("SERVER_URL")

def main():
   
    #CLIENT INITIALIZATION
    try:
        client = SyncFHIRClient(SERVER_URL)
    except Exception as e:
        print(f"Error: Could not create client. {e}")
        sys.exit(1)

    #FETCH DATA (all patients)
    try:
        patients = client.resources('Patient') \
            .sort('_lastUpdated') \
            .limit(1) \
            .fetch()
            #.fetch_all()                
    except Exception as e:
        print(f"Connection Error: {e}")
        sys.exit(1)

    #CHECK IF THERE ARE NO PATIENTS IN SERVER
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

    if selected_patient:
        medication_map = {} 
        try:
            med_bundle = client.resources('MedicationRequest').search(patient=selected_patient.id).include('MedicationRequest', 'medication').fetch_raw()
            if med_bundle and med_bundle.entry:
                for entry in med_bundle.entry:
                    res = entry.resource
                    if res.resource_type == 'Medication':
                        try:
                            app_med = AppMedication(res.serialize())
                            medication_map[res.id] = app_med
                        except Exception as e:
                            print(f"[WARNING] Could not parse Medication {res.id}: {e}")
        except Exception as e:
            print(f"[ERROR] Error fetching medications map: {e}")

        resource_configs = [
            ('Device',            AppDevice,            selected_patient.add_devices),
            ('AllergyIntolerance',AppAllergyIntolerance,selected_patient.add_allergies),
            ('CarePlan',          AppCarePlan,          selected_patient.add_care_plans),
            ('Condition',         AppCondition,         selected_patient.add_conditions),
            ('Procedure',         AppProcedure,         selected_patient.add_procedures),
            ('DiagnosticReport',  AppDiagnosticReport,  selected_patient.add_diagnostic_reports),
            ('DocumentReference', AppDocumentReference, selected_patient.add_document_references),
            ('Observation',       AppObservation,       selected_patient.add_observations),
            ('Immunization',      AppImmunization,      selected_patient.add_immunizations),
            ('MedicationRequest', AppMedicationRequest, selected_patient.add_medication_requests)
        ]

        for resource_type, AppClass, add_method in resource_configs:
            fetched_resources = []
            try:
                fetched_resources = client.resources(resource_type) \
                    .search(patient=selected_patient.id) \
                    .sort('-_lastUpdated') \
                    .fetch_all()
            except Exception as e:
                print(f"[ERROR] Error fetching {resource_type} for patient {selected_patient.id}: {e}")
                continue 

            app_objects = []
            for res in fetched_resources:
                try:
                    app_obj = AppClass(res.serialize())
                    app_objects.append(app_obj)
                except Exception as e:
                    r_id = res.id if hasattr(res, 'id') else "Unknown"
                    print(f"[WARNING] Could not parse {resource_type} {r_id}: {e}")

            add_method(app_objects)

        print(selected_patient.generate_clinical_context(medication_map))
    
    else:
        print(f"Patient with ID {target_id} not found.")

    
    
if __name__ == "__main__":
    main()