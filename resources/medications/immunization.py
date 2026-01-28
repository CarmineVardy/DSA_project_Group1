from fhir.resources.immunization import Immunization as FhirImmunization
from fhir.resources.codeableconcept import CodeableConcept
from typing import Optional, List, Dict, Union, Any
from datetime import date, datetime

class AppImmunization:
    
    # --- Use Cases lists---
    uc1_selected_resources = [
        "Influenza, seasonal, injectable, preservative free"
    ]

    uc2_selected_resources = [
        "Hep A, adult",
        "Hep B, adult",
        "Pneumococcal conjugate PCV 13",
        "Td (adult) preservative free",
        "meningococcal MCV4P",
        "pneumococcal polysaccharide vaccine, 23 valent",
        "zoster"
    ]

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

    # --- USE CASE FILTERING ---
    
    def check_is_selected(self, use_case: str) -> bool:
        """
        Checks if this Immunization is in the selected list for the given use case.
        Arguments:
            use_case (str): "uc1" or "uc2"
        """
        current_name = self.vaccineCode.strip()
        target_list = []

        if use_case.lower() == "uc1":
            target_list = self.uc1_selected_resources
        elif use_case.lower() == "uc2":
            target_list = self.uc2_selected_resources
        else:
            return False

        # Check for exact match or substring match
        for item in target_list:
            if item.lower() == current_name.lower():
                return True
        return False

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


    """
    Returns a comprehensive list of all the elements specified in this class.
    Formatted as 'Element: value'
    """
    def __str__(self):

        lines = [
            f"ID: {self.id}",
            f"Status: {self.status}",
            f"Vaccine Code: {self.vaccineCode}",
            f"Occurrence Display: {self.occurrence_display}"
        ]
        return "\n".join(lines)