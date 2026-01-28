from fhir.resources.procedure import Procedure as FhirProcedure
from fhir.resources.codeableconcept import CodeableConcept
from typing import Optional, List, Dict, Union, Any
from datetime import datetime

class AppProcedure:
    
    # ---------------------------------------------------------
    # USE CASE CONFIGURATION
    # ---------------------------------------------------------
    uc1_selected_resources = [
        "Renal dialysis",
        "Coronary artery bypass",
        "Percutaneous coronary intervention (Stent)",
        "Laparoscopic Removal Gall Bladder",
        "Chemotherapy"
    ]

    uc2_selected_resources = [
        "Renal dialysis",
        "Coronary artery bypass",
        "Percutaneous coronary intervention (Stent)",
        "Chemotherapy"
    ]

    def __init__(self, raw_json_data: dict):
        self.raw = raw_json_data
        
        # COMPATIBILITY LAYER:
        # Translate R4/STU3 field names to R5 standard so the library accepts them
        # without losing the data.
        translated_data = self._apply_compatibility_layer(raw_json_data)
        
        self.resource = FhirProcedure(**translated_data)

    def _apply_compatibility_layer(self, data: dict) -> dict:
        """
        Interface function that translates R4/STU3 keys to R5 keys.
        This allows the strict R5 Pydantic model to validate R4 data successfully.
        """
        # Create a shallow copy to avoid modifying the original dictionary reference
        data_copy = data.copy()

        # Map: R4 Name -> R5 Name
        # We pop the old key and insert the new key if it doesn't exist
        mapping = {
            'performedPeriod': 'occurrencePeriod',
            'performedDateTime': 'occurrenceDateTime',
            'performedString': 'occurrenceString',
            'performedAge': 'occurrenceAge',
            'performedRange': 'occurrenceRange'
        }

        for r4_key, r5_key in mapping.items():
            if r4_key in data_copy:
                # Move data to the new key expected by the library
                data_copy[r5_key] = data_copy.pop(r4_key)
        
        # Note: 'reasonReference' exists in R4 but was removed in R5 (merged into reasonCode or supportingInfo).
        # To avoid validation error in R5 library, we must handle it. 
        # Since we can't easily map it to a list of CodeableConcepts (reasonCode), 
        # we act defensively: if present, we remove it from the validation dict
        # but we can still access it via self.raw in the properties if needed.
        if 'reasonReference' in data_copy:
            del data_copy['reasonReference']

        return data_copy

    # ---------------------------------------------------------
    # PROPERTIES
    # ---------------------------------------------------------

    @property
    def id(self) -> str:
        return self.resource.id

    @property
    def status(self) -> str:
        # preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown
        return self.resource.status

    @property
    def code(self) -> str:
        # The specific procedure code (e.g., Appendectomy)
        return self._get_concept_display(self.resource.code) or "Unknown Procedure"

    @property
    def category(self) -> Optional[str]:
        # Classification (e.g., Surgical, Diagnostic)
        return self._get_concept_display(self.resource.category)

    @property
    def occurrenceDateTime(self) -> Optional[datetime]:
        # Thanks to the compatibility layer, R4 'performedDateTime' is now here
        return self.resource.occurrenceDateTime

    @property
    def occurrencePeriod(self) -> Optional[Dict[str, datetime]]:
        # Thanks to the compatibility layer, R4 'performedPeriod' is now here
        if self.resource.occurrencePeriod:
            return {
                "start": self.resource.occurrencePeriod.start,
                "end": self.resource.occurrencePeriod.end
            }
        return None

    @property
    def occurrence_display(self) -> str:
        # Helper to get a readable string regardless of whether it is a DateTime or Period
        if self.occurrenceDateTime:
            return self.occurrenceDateTime.strftime("%Y-%m-%d")
        
        if self.occurrencePeriod:
            start = self.occurrencePeriod['start'].strftime("%Y-%m-%d") if self.occurrencePeriod['start'] else "?"
            end = self.occurrencePeriod['end'].strftime("%Y-%m-%d") if self.occurrencePeriod['end'] else "?"
            return f"{start} to {end}"

        return "Unknown Date"

    @property
    def reasons(self) -> List[str]:
        # Consolidates reasonReference (from raw R4) and reasonCode (from resource R5)
        reasons_list = []

        # 1. Check strict R5 reasonCode
        if self.resource.reasonCode:
            for code in self.resource.reasonCode:
                display = self._get_concept_display(code)
                if display:
                    reasons_list.append(display)

        # 2. Check raw R4 reasonReference (since we stripped it from validation)
        if 'reasonReference' in self.raw:
            for ref in self.raw['reasonReference']:
                if isinstance(ref, dict):
                    if ref.get('display'):
                        reasons_list.append(ref['display'])
                    elif ref.get('reference'):
                        reasons_list.append(f"Ref: {ref['reference']}")
        
        return reasons_list

    @property
    def bodySite(self) -> List[str]:
        if self.resource.bodySite:
            return [self._get_concept_display(site) for site in self.resource.bodySite]
        return []
    
    @property
    def outcome(self) -> Optional[str]:
        return self._get_concept_display(self.resource.outcome)

    @property
    def complications(self) -> List[str]:
        if self.resource.complication:
            return [self._get_concept_display(comp) for comp in self.resource.complication]
        return []

    # ---------------------------------------------------------
    # METHODS
    # ---------------------------------------------------------

    """
    Checks if the current procedure is in the selected Use Case list.
    uc_type: "uc1" or "uc2"
    """
    def is_relevant_for_uc(self, uc_type: str) -> bool:
        current_procedure_name = self.code.lower().strip()
        
        target_list = []
        if uc_type.lower() == "uc1":
            target_list = self.uc1_selected_resources
        elif uc_type.lower() == "uc2":
            target_list = self.uc2_selected_resources
        else:
            return False

        # Check if the procedure name corresponds to any in the list (fuzzy match)
        # We check if the target string is contained in the procedure code display
        for item in target_list:
            if item.lower() in current_procedure_name:
                return True
            # Also check exact match or if the procedure contains the item text
            if current_procedure_name in item.lower():
                return True
                
        return False

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
        if not isinstance(other, AppProcedure):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
    
    
    """
    Returns a comprehensive list of all elements specified in this class.
    Format: [Element]: [value]
    """
    def __str__(self):

        lines = [
            f"ID: {self.id}",
            f"Code: {self.code}",
            f"Status: {self.status}",
            f"Category: {self.category or 'None'}",
            f"Occurrence: {self.occurrence_display}",
            f"Occurrence Period: {self.occurrencePeriod}", 
            f"Occurrence DateTime: {self.occurrenceDateTime}",
            f"Body Site: {', '.join(self.bodySite) or 'None'}",
            f"Outcome: {self.outcome or 'None'}",
            f"Complications: {', '.join(self.complications) or 'None'}",
            f"Reasons: {', '.join(self.reasons) or 'None'}"            
        ]
        return "\n".join(lines)