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

    #only if selected_patient != None

    #MEDICATION
    medication_map = {} 
    try:
        med_bundle = client.resources('MedicationRequest') \
            .search(patient=selected_patient.id) \
            .include('MedicationRequest', 'medication') \
            .fetch_raw()
        if med_bundle and med_bundle.entry:
            for entry in med_bundle.entry:
                res = entry.resource
                if res.resource_type == 'Medication':
                    try:
                        app_med = AppMedication(res.serialize())
                        medication_map[res.id] = app_med
                    except Exception as e:
                        print(f"[WARNING] Could not parse Medication {res.id}: {e}")
        print(f"DEBUG: Loaded {len(medication_map)} medications into map.")
    except Exception as e:
        print(f"[ERROR] Error fetching medications: {e}")

    #DEVICE
    devices = []
    try:
        devices = client.resources('Device') \
            .search(patient=selected_patient.id) \
            .sort('-_lastUpdated') \
            .fetch_all()
    except Exception as e:
        print(f"[ERROR] Error fetching devices for patient {selected_patient.id}: {e}")

    app_devices = []
    for device in devices:
        try:
            app_dev = AppDevice(device.serialize())
            app_devices.append(app_dev)
        except Exception as e:
            d_id = device.id if hasattr(device, 'id') else "Unknown"
            print(f"[WARNING] Could not parse device {d_id} for patient {selected_patient.id}: {e}")

    selected_patient.add_devices(app_devices)

    #ALLERGYINTOLERANCE
    allergies = []
    try:
        allergies = client.resources('AllergyIntolerance') \
            .search(patient=selected_patient.id) \
            .sort('-_lastUpdated') \
            .fetch_all()
    except Exception as e:
        print(f"[ERROR] Error fetching allergies for patient {selected_patient.id}: {e}")

    app_allergies = []
    for allergy in allergies:
        try:
            app_alg = AppAllergyIntolerance(allergy.serialize())
            app_allergies.append(app_alg)
        except Exception as e:
            a_id = allergy.id if hasattr(allergy, 'id') else "Unknown"
            print(f"[WARNING] Could not parse allergy {a_id}: {e}")

    selected_patient.add_allergies(app_allergies)

    #CAREPLAN
    care_plans = []
    try:
        care_plans = client.resources('CarePlan') \
            .search(patient=selected_patient.id) \
            .sort('-_lastUpdated') \
            .fetch_all()
    except Exception as e:
        print(f"[ERROR] Error fetching care plans for patient {selected_patient.id}: {e}")

    app_care_plans = []
    for plan in care_plans:
        try:
            app_plan = AppCarePlan(plan.serialize())
            app_care_plans.append(app_plan)
        except Exception as e:
            cp_id = plan.id if hasattr(plan, 'id') else "Unknown"
            print(f"[WARNING] Could not parse care plan {cp_id} for patient {selected_patient.id}: {e}")

    selected_patient.add_care_plans(app_care_plans)

    #CONDITION
    conditions = []
    try:
        conditions = client.resources('Condition') \
            .search(patient=selected_patient.id) \
            .sort('-_lastUpdated') \
            .fetch_all()
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

    #PROCEDURE
    procedures = []
    try:
        procedures = client.resources('Procedure') \
            .search(patient=selected_patient.id) \
            .sort('-_lastUpdated') \
            .fetch_all()
    except Exception as e:
        print(f"[ERROR] Error fetching procedures for patient {selected_patient.id}: {e}")

    app_procedures = []
    for proc in procedures:
        try:
            app_proc = AppProcedure(proc.serialize())
            app_procedures.append(app_proc)
        except Exception as e:
            p_id = proc.id if hasattr(proc, 'id') else "Unknown"
            print(f"[WARNING] Could not parse procedure {p_id} for patient {selected_patient.id}: {e}")

    selected_patient.add_procedures(app_procedures)

    #DIAGNOSTICREPORT
    diagnostic_reports = []
    try:
        diagnostic_reports = client.resources('DiagnosticReport') \
            .search(patient=selected_patient.id) \
            .sort('-_lastUpdated') \
            .fetch_all()
    except Exception as e:
        print(f"[ERROR] Error fetching diagnostic reports for patient {selected_patient.id}: {e}")

    app_diagnostic_reports = []
    for report in diagnostic_reports:
        try:
            app_rep = AppDiagnosticReport(report.serialize())
            app_diagnostic_reports.append(app_rep)
        except Exception as e:
            r_id = report.id if hasattr(report, 'id') else "Unknown"
            print(f"[WARNING] Could not parse diagnostic report {r_id} for patient {selected_patient.id}: {e}")

    selected_patient.add_diagnostic_reports(app_diagnostic_reports)

    #DOCUMENTREFERENCE
    docs = []
    try:
        docs = client.resources('DocumentReference') \
            .search(patient=selected_patient.id) \
            .sort('-_lastUpdated') \
            .fetch_all()
    except Exception as e:
        print(f"[ERROR] Error fetching document references for patient {selected_patient.id}: {e}")

    app_docs = []
    for doc in docs:
        try:
            app_doc = AppDocumentReference(doc.serialize())
            app_docs.append(app_doc)
        except Exception as e:
            d_id = doc.id if hasattr(doc, 'id') else "Unknown"
            print(f"[WARNING] Could not parse document reference {d_id} for patient {selected_patient.id}: {e}")

    selected_patient.add_document_references(app_docs)

    #OBSERVATION
    observations = []
    try:
        observations = client.resources('Observation') \
            .search(patient=selected_patient.id) \
            .sort('-_lastUpdated') \
            .fetch_all()
    except Exception as e:
        print(f"[ERROR] Error fetching observations for patient {selected_patient.id}: {e}")

    app_observations = []
    for obs in observations:
        try:
            app_obs = AppObservation(obs.serialize())
            app_observations.append(app_obs)
        except Exception as e:
            o_id = obs.id if hasattr(obs, 'id') else "Unknown"
            print(f"[WARNING] Could not parse observation {o_id}: {e}")

    selected_patient.add_observations(app_observations)

    #IMMUNIZATION
    immunizations = []
    try:
        immunizations = client.resources('Immunization') \
            .search(patient=selected_patient.id) \
            .sort('-_lastUpdated') \
            .fetch_all()
    except Exception as e:
        print(f"[ERROR] Error fetching immunizations for patient {selected_patient.id}: {e}")

    app_immunizations = []
    for imm in immunizations:
        try:
            app_imm = AppImmunization(imm.serialize())
            app_immunizations.append(app_imm)
        except Exception as e:
            i_id = imm.id if hasattr(imm, 'id') else "Unknown"
            print(f"[WARNING] Could not parse immunization {i_id} for patient {selected_patient.id}: {e}")

    selected_patient.add_immunizations(app_immunizations)

    #MEDICATIONREQUESTS
    med_requests = []
    try:
        med_requests = client.resources('MedicationRequest') \
            .search(patient=selected_patient.id) \
            .sort('-_lastUpdated') \
            .fetch_all()
    except Exception as e:
        print(f"[ERROR] Error fetching medication requests for patient {selected_patient.id}: {e}")

    app_med_requests = []
    for req in med_requests:
        try:
            app_req = AppMedicationRequest(req.serialize())
            app_med_requests.append(app_req)        
        except Exception as e:
            r_id = req.id if hasattr(req, 'id') else "Unknown"
            print(f"[WARNING] Could not parse medication request {r_id} for patient {selected_patient.id}: {e}")

    selected_patient.add_medication_requests(app_med_requests)

    
    print(selected_patient.generate_clinical_context())

    
    


if __name__ == "__main__":
    main()