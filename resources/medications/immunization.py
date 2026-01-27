from fhir.resources.immunization import Immunization as FhirImmunization
from fhir.resources.codeableconcept import CodeableConcept
from typing import Optional, List, Dict, Union, Any
from datetime import date, datetime

class AppImmunization:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirImmunization(**raw_json_data)

    @property
    def id(self) -> str:
        return self.resource.id


    # completed | entered-in-error | not-done
    @property
    def status(self) -> str:
        return self.resource.status


    # Vaccine product administered (e.g. 'Influenza, seasonal')
    @property
    def vaccineCode(self) -> str:
        return self._get_concept_display(self.resource.vaccineCode) or "Unknown Vaccine"

    # --- SPECIFIC DETAILS ---
    # Returns datetime object if specific time is known, otherwise the string representation
    @property
    def occurrence(self) -> Union[datetime, str, None]:
        if self.resource.occurrenceDateTime:
            return self.resource.occurrenceDateTime # There are no occurrenceString in the immunization resources
        return None

    # Helper for UI display
    @property
    def occurrence_display(self) -> str:
        val = self.occurrence
        if isinstance(val, (datetime, date)):
            return val.strftime("%Y-%m-%d")
        return str(val) if val else "Unknown Date"

    # --- UTIL METHODS ---
    # Helper to safely extract display text from a FHIR CodeableConcept
    # Priority: text -> coding.display -> None
    def _get_concept_display(self, codeable_concept: Optional[CodeableConcept]) -> Optional[str]:
        if not codeable_concept:
            return None
        if codeable_concept.text:
            return codeable_concept.text
        if codeable_concept.coding:
            for coding in codeable_concept.coding:
                if coding.display:
                    return coding.display
        return None

    def __eq__(self, other):
        if not isinstance(other, AppImmunization):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    # Returns: [Date] Vaccine Name (Status)
    def __str__(self):
        return f"[{self.occurrence_display}] {self.vaccineCode} ({self.status})"