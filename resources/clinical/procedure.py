from fhir.resources.procedure import Procedure as FhirProcedure
from fhir.resources.codeableconcept import CodeableConcept
from typing import Optional, List, Dict, Union, Any
from datetime import datetime

class AppProcedure:
    def __init__(self, raw_json_data: dict):
        self.raw = raw_json_data
        
        # Create a safe copy for validation
        # We remove fields that are known to cause version-mismatch errors in Pydantic
        # (performedPeriod is R4/STU3, but library expects occurrencePeriod)
        safe_data = raw_json_data.copy()
        keys_to_remove = ['performedPeriod', 'performedDateTime', 'reasonReference']
        for key in keys_to_remove:
            if key in safe_data:
                del safe_data[key]

        self.resource = FhirProcedure(**safe_data)

    @property
    def id(self) -> str:
        return self.resource.id

    # preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown
    @property
    def status(self) -> str:
        return self.resource.status

    # The specific procedure code (e.g., Appendectomy) - Important for __str__.        
    @property
    def code(self) -> str:
        return self._get_concept_display(self.resource.code) or "Unknown Procedure"

    # Classification of the procedure (e.g., Surgical, Diagnostic, Chiropractic)
    @property
    def category(self) -> Optional[str]:
        return self._get_concept_display(self.resource.category)

    # --- OCCURRENCE LOGIC (DateTime or Period) ---
    @property
    def occurrenceDateTime(self) -> Optional[datetime]:
        return self.resource.occurrenceDateTime

    # Returns a dict with 'start' and 'end' if available
    @property
    def occurrencePeriod(self) -> Optional[Dict[str, datetime]]:
        # Try resource first
        if self.resource.occurrencePeriod:
            return {
                "start": self.resource.occurrencePeriod.start,
                "end": self.resource.occurrencePeriod.end
            }
        
        # Fallback to raw data for performedPeriod (which was stripped)
        if 'performedPeriod' in self.raw:
            p = self.raw['performedPeriod']
            # Note: These are strings in raw dict, not datetime objects
            return {
                "start": p.get('start'), 
                "end": p.get('end')
            }
        return None

    # Helper to get a readable string regardless of whether it is a DateTime or Period
    @property
    def occurrence_display(self) -> str:
        # 1. Try strict library fields
        if self.occurrenceDateTime:
            return self.occurrenceDateTime.strftime("%Y-%m-%d")
        
        if self.resource.occurrencePeriod:
            start = self.resource.occurrencePeriod.start
            end = self.resource.occurrencePeriod.end
            return f"{start} to {end}"

        p_period = self.raw.get('performedPeriod')
        if p_period:
            start = p_period.get('start', '?').split('T')[0]
            end = p_period.get('end', '?').split('T')[0]
            return f"{start} to {end}"
            
        return "Unknown Date"


    # Consolidates reasonReference (references to Conditions/Observations)
    @property
    def reasons(self) -> List[str]:
        reasons_list = []

        # Reason References (Manually from raw if stripped, or resource if present)
        # Check resource first
        if self.resource.reasonReference:
            for ref in self.resource.reasonReference:
                if ref.display:
                    reasons_list.append(ref.display)
                elif ref.reference:
                    reasons_list.append(f"Ref: {ref.reference}")
        # Check raw if resource is empty but raw has it
        elif 'reasonReference' in self.raw:
            for ref in self.raw['reasonReference']:
                if ref.get('display'):
                     reasons_list.append(ref['display'])
                elif ref.get('reference'):
                     reasons_list.append(f"Ref: {ref['reference']}")
        
        return reasons_list


    # --- UTIL METHODS ---
    # Helper to safely extract display text from a FHIR CodeableConcept
    # Priority: text -> coding.display -> None
    def _get_concept_display(self, codeable_concept: Optional[CodeableConcept]) -> Optional[str]:
        if not codeable_concept:
            return None
        
        # Priority 1: Free text description
        if codeable_concept.text:
            return codeable_concept.text
        
        # Priority 2: Structured coding display
        if codeable_concept.coding:
            # Return the first available display name
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
        Returns: [Date] Procedure Name (Status)
        e.g., "2023-10-12 Appendectomy (completed)"
    """
    def __str__(self):
        date_str = self.occurrence_display
        return f"[{date_str}] {self.code} ({self.status})"