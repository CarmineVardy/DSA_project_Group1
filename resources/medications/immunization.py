'''
Script: immunization.py
Digital Health Systems and Applications - Project work 2025-2026
Description:
Wrapper class for the HL7 FHIR Immunization resource. It handles vaccination status,
vaccine codes, and administration dates, providing standardized output for the
patient's immunization history.

Group: Carmine Vardaro, Marco Savastano, Francesco Ferrara.
'''

from fhir.resources.immunization import Immunization as FhirImmunization
from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime

from resources.core.types import AppCodeableConcept

class ImmunizationStatus(str, Enum):
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    NOT_DONE = "not-done"

    @property
    def definition(self) -> str:
        # https://hl7.org/fhir/R4/valueset-immunization-status.html
        definitions = {
            "completed": "The event has now concluded.",
            "entered-in-error": 'This electronic record should never have existed, though it is possible that real-world decisions were based on it. (If real-world activity has occurred, the status should be "stopped" rather than "entered-in-error".).',
            "not-done": "The event was terminated prior to any activity beyond preparation. I.e. The 'main' activity has not yet begun. The boundary between preparatory and the 'main' activity is context-specific."
        }
        return definitions.get(self.value, "Definition not available.")

class AppImmunization:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirImmunization(**raw_json_data)

    @property
    def id(self):
        return self.resource.id

    @property
    def status(self) -> Optional[ImmunizationStatus]:
        if not self.resource.status:
            return None
        try:
            return ImmunizationStatus(self.resource.status)
        except ValueError:
            return None

    @property
    def code_text(self) -> Optional[str]:
        if not self.resource.vaccineCode:
            return None
        return AppCodeableConcept(self.resource.vaccineCode).readable_value

    @property
    def code_details(self) -> List[Dict[str, Optional[str]]]:
        if not self.resource.vaccineCode:
            return []    
        return AppCodeableConcept(self.resource.vaccineCode).coding_details

    @property
    def occurrence_date(self) -> Optional[datetime]:
        return self.resource.occurrenceDateTime

    @property
    def simple_code_str(self) -> str:
        """
        Helper property to facilitate grouping by generating a standard code string.
        """
        if self.code_details:
            code_parts = []
            for c in self.code_details:
                # Direct syntax formatting
                code_parts.append(f"[{c['system']}: {c['code']}]")
            return " " + " ".join(code_parts)
        return ""

    def to_prompt_string(self) -> str:
        # Fallback method (used if grouping is not applied)
        header_name = self.code_text or "Unknown Vaccine"
        
        date_str = ""
        if self.occurrence_date:
            date_str = f" [Date: {self.occurrence_date.strftime('%Y-%m-%d')}]"
            
        return f"- {header_name}{date_str}{self.simple_code_str}"