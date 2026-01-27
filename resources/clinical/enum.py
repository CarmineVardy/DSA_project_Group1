from enum import Enum

# ==========================================
# CONDITION ENUMS
# ==========================================

class ClinicalStatus(str, Enum):
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

class VerificationStatus(str, Enum):
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