'''
Script: medication.py
Digital Health Systems and Applications - Project work 2025-2026
Description:
Wrapper class for the HL7 FHIR Medication resource. It extracts medication names
and coding details to be referenced by MedicationRequests.

Group: Carmine Vardaro, Marco Savastano, Francesco Ferrara.
'''

from fhir.resources.medication import Medication as FhirMedication
from typing import Optional, List, Dict

from resources.core.types import AppCodeableConcept

class AppMedication:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirMedication(**raw_json_data)

    @property
    def id(self) -> str:
        return self.resource.id

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
    def simple_code_str(self) -> str:
        """
        Helper property to generate a standardized code string.
        """
        if self.code_details:
            code_parts = []
            for c in self.code_details:
                code_parts.append(f"[{c['system']}: {c['code']}]")
            return " " + " ".join(code_parts)
        return ""

    def to_prompt_string(self) -> str:
        name = self.code_text or "Unknown Medication"
        return f"{name}{self.simple_code_str}"