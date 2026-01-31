from fhir.resources.patient import Patient as FhirPatient

from datetime import date, datetime
from enum import Enum
from typing import Optional, List

from resources.administration.device import AppDevice
from resources.clinical.allergyIntolerance import AppAllergyIntolerance
from resources.clinical.carePlan import AppCarePlan
from resources.clinical.condition import AppCondition
from resources.clinical.procedure import AppProcedure
from resources.diagnostics.diagnosticReport import AppDiagnosticReport
from resources.diagnostics.documentReference import AppDocumentReference
from resources.diagnostics.observation import AppObservation
from resources.medications.immunization import AppImmunization
from resources.medications.medicationRequests import AppMedicationRequest

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"
    
class AppPatient:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirPatient(**raw_json_data)
        self._devices: List[AppDevice] = []
        self._allergies: List[AppAllergyIntolerance] = []
        self._care_plans: List[AppCarePlan] = []
        self._conditions: List[AppCondition] = []
        self._procedures: List[AppProcedure] = []
        self._diagnostic_reports: List[AppDiagnosticReport] = []
        self._document_references: List[AppDocumentReference] = []
        self._observations: List[AppObservation] = []
        self._immunizations: List[AppImmunization] = []
        self._medication_requests: List[AppMedicationRequest] = []
        
    @property
    def id(self):
        return self.resource.id

    @property
    def gender(self) -> Gender:
        if not self.resource.gender:
            return None
        try:
            return Gender(self.resource.gender)
        except ValueError:
            return None

    @property
    def birth_date(self) -> Optional[date]:
        return self.resource.birthDate

    @property
    def age(self) -> int:
        if not self.birth_date:
            return -1
        born = self.birth_date
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @property
    def is_deceased(self) -> bool:
        if self.resource.deceasedDateTime:
            return True
        if self.resource.deceasedBoolean is True:
            return True
        return False

    @property
    def deceased_date(self) -> Optional[datetime]:
        if not self.isDeceased:
            return None
        return self.resource.deceasedDateTime

    @property  
    def full_name(self) -> str:
        #If no name
        if not self.resource.name:
            return "Unknown"
        #Take all the names
        formatted_names = [
            f"{' '.join(n.given or [])} {n.family or ''}".strip() or "(Unnamed)"
            for n in self.resource.name
        ]
        #If one name return it
        if len(formatted_names) == 1:
            return formatted_names[0]
        #If more than one name build the string with all
        sfx = {1: 'st', 2: 'nd', 3: 'rd'}
        return "\n".join(f"{i}{sfx.get(i if i < 20 else i % 10, 'th')}: {name}" for i, name in enumerate(formatted_names, 1))
    
    @property
    def devices(self) -> List[AppDevice]:
        return self._devices

    def add_devices(self, devices: List[AppDevice]):
        self._devices.extend(devices)

    @property
    def allergies(self) -> List[AppAllergyIntolerance]:
        return self._allergies

    def add_allergies(self, allergies: List[AppAllergyIntolerance]):
        self._allergies.extend(allergies)

    @property
    def care_plans(self) -> List[AppCarePlan]:
        return self._care_plans

    def add_care_plans(self, plans: List[AppCarePlan]):
        self._care_plans.extend(plans)

    @property
    def conditions(self) -> List[AppCondition]:
        return self._conditions

    def add_conditions(self, conditions: List[AppCondition]):
        self._conditions.extend(conditions)

    @property
    def procedures(self) -> List[AppProcedure]:
        return self._procedures

    def add_procedures(self, procedures: List[AppProcedure]):
        self._procedures.extend(procedures)

    @property
    def diagnostic_reports(self) -> List[AppDiagnosticReport]:
        return self._diagnostic_reports

    def add_diagnostic_reports(self, reports: List[AppDiagnosticReport]):
        self._diagnostic_reports.extend(reports)

    @property
    def document_references(self) -> List[AppDocumentReference]:
        return self._document_references

    def add_document_references(self, docs: List[AppDocumentReference]):
        self._document_references.extend(docs)

    @property
    def observations(self) -> List[AppObservation]:
        return self._observations

    def add_observations(self, observations: List[AppObservation]):
        self._observations.extend(observations)

    @property
    def immunizations(self) -> List[AppImmunization]:
        return self._immunizations

    def add_immunizations(self, immunizations: List[AppImmunization]):
        self._immunizations.extend(immunizations)

    @property
    def medication_requests(self) -> List[AppMedicationRequest]:
        return self._medication_requests

    def add_medication_requests(self, requests: List[AppMedicationRequest]):
        self._medication_requests.extend(requests)

    def generate_clinical_context(self) -> str:
        context_parts = []
        
        context_parts.append("### PATIENT CLINICAL SUMMARY")
                
        #DEMOGRAPHICS
        gender_str = self.gender.value if self.gender else "Unknown"
        age_str = f"{self.age} years old" if self.age >= 0 else "Age unknown"
        context_parts.append(f"- Demographics: {gender_str}, {age_str}")

        


        return "\n".join(context_parts)