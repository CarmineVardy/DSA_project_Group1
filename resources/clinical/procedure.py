'''
Script: procedure.py
Digital Health Systems and Applications - Project work 2025-2026
Description:
Wrapper class for the HL7 FHIR Procedure resource. It manages procedure status,
categories, codes, and performance dates. It also provides helper properties for
grouping procedures in the patient summary.

Group: Carmine Vardaro, Marco Savastano, Francesco Ferrara.
'''

from fhir.resources.procedure import Procedure as FhirProcedure

from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime

from resources.core.types import AppCodeableConcept

class ProcedureStatus(str, Enum):
    PREPARATION = "preparation"
    IN_PROGRESS = "in-progress"
    NOT_DONE = "not-done"
    ON_HOLD = "on-hold"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"

    @property
    def definition(self) -> str:
        # https://hl7.org/fhir/R4/valueset-event-status.html
        definitions = {
            "preparation": "The core event has not started yet, but some staging activities have begun (e.g. surgical suite preparation). Preparation stages may be tracked for billing purposes.",
            "in-progress": "The event is currently occurring.",
            "not-done": "The event was terminated prior to any activity beyond preparation. I.e. The 'main' activity has not yet begun. The boundary between preparatory and the 'main' activity is context-specific.",
            "on-hold": "The event has been temporarily stopped but is expected to resume in the future.",
            "stopped": "The event was terminated prior to the full completion of the intended activity but after at least some of the 'main' activity (beyond preparation) has occurred.",
            "completed": "The event has now concluded.",
            "entered-in-error": 'This electronic record should never have existed, though it is possible that real-world decisions were based on it. (If real-world activity has occurred, the status should be "stopped" rather than "entered-in-error".).',
            "unknown": 'The authoring/source system does not know which of the status values currently applies for this event. Note: This concept is not to be used for "other" - one of the listed statuses is presumed to apply, but the authoring/source system does not know which.'
        }
        return definitions.get(self.value, "Definition not available.")

class AppProcedure:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirProcedure(**raw_json_data)

    @property
    def id(self):
        return self.resource.id

    @property
    def status(self) -> Optional[ProcedureStatus]:
        if not self.resource.status:
            return None
        try:
            return ProcedureStatus(self.resource.status)
        except ValueError:
            return None

    @property
    def category_text(self) -> Optional[str]:
        if not self.resource.category:
            return None
        return AppCodeableConcept(self.resource.category).readable_value

    @property
    def category_details(self) -> List[Dict[str, Optional[str]]]:
        if not self.resource.category:
            return []    
        return AppCodeableConcept(self.resource.category).coding_details

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
    def start_date(self) -> Optional[datetime]:
        if self.resource.performedPeriod and self.resource.performedPeriod.start:
            return self.resource.performedPeriod.start
        return None

    @property
    def end_date(self) -> Optional[datetime]:
        if self.resource.performedPeriod and self.resource.performedPeriod.end:
            return self.resource.performedPeriod.end
        return None

    @property
    def simple_code_str(self) -> str:
        """
        Helper property to generate a standardized code string for grouping purposes.
        """
        if self.code_details:
            code_parts = []
            for c in self.code_details:
                # Direct syntax formatting
                code_parts.append(f"[{c['system']}: {c['code']}]")
            return " " + " ".join(code_parts)
        return ""

    def to_prompt_string(self) -> str:
        # Fallback method (used for single instance printing)
        name = self.code_text or "Unknown Procedure"

        date_str = ""
        if self.start_date:
            date_str = f" [Date: {self.start_date.strftime('%Y-%m-%d')}]"
            
        return f"- {name}{date_str}{self.simple_code_str}"