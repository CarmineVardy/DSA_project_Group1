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

    # 4. PROMPT GENERATION
    def to_prompt_string(self) -> str:
        header_name = self.code_text
        
        # Se non c'è nome né codici, la risorsa è inutile
        if not header_name and not self.code_details:
            return ""

        meta_parts = []
        if self.status:
            meta_parts.append(self.status.value.capitalize())

        meta_str = f" ({', '.join(meta_parts)})" if meta_parts else ""

        date_str = ""
        if self.occurrence_date:
            date_str = f" [{self.occurrence_date.strftime('%Y-%m-%d')}]"
        
        header_line = f"- {header_name or 'Unknown Vaccine'}{meta_str}{date_str}"

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