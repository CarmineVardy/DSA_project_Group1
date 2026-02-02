'''
Script: condition.py
Digital Health Systems and Applications - Project work 2025-2026
Description:
Wrapper class for the HL7 FHIR Condition resource. It handles clinical status, verification status,
and categories, formatting the condition details (onset, codes, etc.) for the clinical context.

Group: Carmine Vardaro, Marco Savastano, Francesco Ferrara.
'''

from fhir.resources.condition import Condition as FhirCondition

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict

from resources.core.types import AppCodeableConcept

class ConditionClinicalStatus(str, Enum):
    ACTIVE = "active"
    RECURRENCE = "recurrence"
    RELAPSE = "relapse"
    INACTIVE = "inactive"
    REMISSION = "remission"
    RESOLVED = "resolved"
    UNKNOWN = "unknown"

    @property
    def definition(self) -> str:
        #https://terminology.hl7.org/7.0.1/CodeSystem-condition-clinical.html
        definitions = {
            "active": "The subject is currently experiencing the condition or situation, there is evidence of the condition or situation, or considered to be a significant risk.",
            "recurrence": "The subject is experiencing a reoccurence or repeating of a previously resolved condition or situation, e.g. urinary tract infection, food insecurity.",
            "relapse": "The subject is experiencing a return of a condition or situation after a period of improvement or remission, e.g. relapse of cancer, alcoholism.",
            "inactive": "The subject is no longer experiencing the condition or situation and there is no longer evidence or appreciable risk of the condition or situation.",
            "remission": "The subject is not presently experiencing the condition or situation, but there is a risk of the condition or situation returning.",
            "resolved": "The subject is not presently experiencing the condition or situation and there is a negligible perceived risk of the condition or situation returning.",
            "unknown": "The authoring/source system does not know which of the status values currently applies for this condition."
        }
        return definitions.get(self.value, "Definition not available.")

class ConditionVerificationStatus(str, Enum):
    UNCONFIRMED = "unconfirmed"
    PROVISIONAL = "provisional"
    DIFFERENTIAL = "differential"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    ENTERED_IN_ERROR = "entered-in-error"

    @property
    def definition(self) -> str:
        #https://terminology.hl7.org/7.0.1/CodeSystem-condition-ver-status.html
        definitions = {
            "unconfirmed": "There is not sufficient diagnostic and/or clinical evidence to treat this as a confirmed condition.",
            "provisional": "This is a tentative diagnosis - still a candidate that is under consideration.",
            "differential": "One of a set of potential (and typically mutually exclusive) diagnoses asserted to further guide the diagnostic process and preliminary treatment.",
            "confirmed": "There is sufficient diagnostic and/or clinical evidence to treat this as a confirmed condition.",
            "refuted": "This condition has been ruled out by subsequent diagnostic and clinical evidence.",
            "entered-in-error": "The statement was entered in error and is not valid.",
        }
        return definitions.get(self.value, "Definition not available.")

class ConditionCategory(str, Enum):
    PROBLEM_LIST_ITEM = "problem-list-item"
    ENCOUNTER_DIAGNOSIS = "encounter-diagnosis"
    DIAGNOSTIC_REPORT_IMPRESSION = "diagnostic-report-impression"

    @property
    def definition(self) -> str:
        #http://terminology.hl7.org/CodeSystem/condition-category
        definitions = {
            "problem-list-item": "An item on a problem list that can be managed over time and can be expressed by a practitioner (e.g. physician, nurse), patient, or related person.",
            "encounter-diagnosis": "A point in time diagnosis (e.g. from a physician or nurse) in context of an encounter.",
        }
        return definitions.get(self.value, "Definition not available.")

class AppCondition:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirCondition(**raw_json_data)

    @property
    def id(self):
        return self.resource.id

    @property
    def clinical_status(self) -> Optional[ConditionClinicalStatus]:
        if not self.resource.clinicalStatus:
            return None    
        return AppCodeableConcept(self.resource.clinicalStatus).bind_to(ConditionClinicalStatus)
    
    @property
    def verification_status(self) -> Optional[ConditionVerificationStatus]:
        if not self.resource.verificationStatus:
            return None 
        return AppCodeableConcept(self.resource.verificationStatus).bind_to(ConditionVerificationStatus)

    @property
    def category(self) -> Optional[ConditionCategory]:
        if not self.resource.category:
            return None
        for cat in self.resource.category:
            found_enum = AppCodeableConcept(cat).bind_to(ConditionCategory)
            if found_enum:
                return found_enum
        return None

    @property
    def code_text(self) -> Optional[str]:
        if not self.resource.code:
            return None
        return AppCodeableConcept(self.resource.code).readable_value

    @property
    def code_details(self) -> List[Dict[str, Optional[str]]]:
        if not self.resource.code:
            return []    
        return AppCodeableConcept(self.resource.code).coding_details

    @property
    def onset_date(self) -> Optional[datetime]:
        return self.resource.onsetDateTime

    @property
    def abatement_date(self) -> Optional[datetime]:
        return self.resource.abatementDateTime

    def to_prompt_string(self) -> str:
        name = self.code_text or "Unknown Condition"

        # Status Management: Print nuances only (Recurrence/Relapse).
        # "Active" is implied as we filter beforehand.
        status_nuance = ""
        if self.clinical_status in [ConditionClinicalStatus.RELAPSE, ConditionClinicalStatus.RECURRENCE]:
             status_nuance = f" ({self.clinical_status.value.capitalize()})"

        # Verification Management: Mention ONLY if "Unconfirmed"
        ver_str = ""
        if self.verification_status == ConditionVerificationStatus.UNCONFIRMED:
            ver_str = " (Unconfirmed)"

        # Date Management: Only Onset. Abatement is irrelevant for active conditions.
        date_str = ""
        if self.onset_date:
            date_str = f" [Onset: {self.onset_date.strftime('%Y-%m-%d')}]"

        # Code Management (Compact syntax)
        code_str = ""
        if self.code_details:
            code_parts = []
            for c in self.code_details:
                code_parts.append(f"[{c['system']}: {c['code']}]")
            
            if code_parts:
                code_str = " " + " ".join(code_parts)

        # Output Example: "- Stroke [Onset: 1993-12-11] [SNOMED: 230690007]"
        return f"- {name}{status_nuance}{ver_str}{date_str}{code_str}"

