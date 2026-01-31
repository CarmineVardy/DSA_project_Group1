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

    def to_prompt_string(self) -> str:
        header_name = self.code_text
        
        if not header_name and not self.code_details:
            return ""

        meta_parts = []
        
        if self.status:
            meta_parts.append(self.status.value.capitalize())
            
        if self.category_text:
            meta_parts.append(self.category_text)

        meta_str = f" ({', '.join(meta_parts)})" if meta_parts else ""

        date_str = ""
        if self.start_date:
            date_str = f" [{self.start_date.strftime('%Y-%m-%d')}]"
        
        header_line = f"- {header_name or ''}{meta_str}{date_str}"

        ref_line = ""
        codes = self.code_details
        if codes:
            code_strs = []
            for c in codes:
                item = f"{c['system']}: {c['code']}"
                #if c.get('display'):
                #    item += f" ({c['display']})"
                code_strs.append(item)
            
            ref_line = f"\n  Ref: {', '.join(code_strs)}"

        return f"{header_line}{ref_line}"