from fhir.resources.procedure import Procedure as FhirProcedure
from fhir.resources.codeableconcept import CodeableConcept
from typing import Optional, List, Dict, Union, Any
from datetime import datetime

class AppProcedure:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirProcedure(**raw_json_data)

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
        if self.resource.occurrencePeriod:
            return {
                "start": self.resource.occurrencePeriod.start,
                "end": self.resource.occurrencePeriod.end
            }
        return None

    # Helper to get a readable string regardless of whether it is a DateTime or Period
    @property
    def occurrence_display(self) -> str:
        if self.occurrenceDateTime:
            return self.occurrenceDateTime.strftime("%Y-%m-%d")
        if self.occurrencePeriod:
            start = self.occurrencePeriod['start'].strftime("%Y-%m-%d") if self.occurrencePeriod['start'] else "?"
            end = self.occurrencePeriod['end'].strftime("%Y-%m-%d") if self.occurrencePeriod['end'] else "?"
            return f"{start} to {end}"
        return "Unknown Date"

    # --- BODY SITE & OUTCOME ---
    # Target body sites (e.g., Left arm, Heart structure)
    @property
    def bodySite(self) -> List[str]:
        if not self.resource.bodySite:
            return []
        return [self._get_concept_display(site) for site in self.resource.bodySite]

    # The result of the procedure (e.g., Successful, Failed)
    @property
    def outcome(self) -> Optional[str]:
        return self._get_concept_display(self.resource.outcome)


    # Instructions or references for follow-up
    @property
    def followUp(self) -> List[str]:
        if not self.resource.followUp:
            return []
        return [self._get_concept_display(item) for item in self.resource.followUp]

    # --- REASONS (Code vs Reference) ---
    # Consolidates reasonCode (coded reasons like 'Pain') and reasonReference (references to Conditions/Observations)
    @property
    def reasons(self) -> List[str]:
        reasons_list = []

        # 1. Reason Codes
        if self.resource.reasonCode:
            for code in self.resource.reasonCode:
                display = self._get_concept_display(code)
                if display:
                    reasons_list.append(display)

        # 2. Reason References (If you have resolved references or just want the display)
        if self.resource.reasonReference:
            for ref in self.resource.reasonReference:
                if ref.display:
                    reasons_list.append(ref.display)
                elif ref.reference:
                    reasons_list.append(f"Ref: {ref.reference}")
        
        return reasons_list

    # --- COMPLICATIONS ---
    # Any complications that occurred during the procedure
    @property
    def complications(self) -> List[str]:
        if not self.resource.complication:
            return []
        return [self._get_concept_display(comp) for comp in self.resource.complication]

    # --- FOCAL DEVICE ---
    # Device changed in procedure
    # Returns list of dicts: {'action': '...', 'manipulated': '...'}
    @property
    def focalDevices(self) -> List[Dict[str, str]]:
        if not self.resource.focalDevice:
            return []

        devices = []
        for device in self.resource.focalDevice:
            # Action: e.g., Implanted, Explanted, Manipulated
            action_str = self._get_concept_display(device.action)
            
            # Manipulated: Reference to the Device resource
            manipulated_str = "Unknown Device"
            if device.manipulated:
                manipulated_str = device.manipulated.display or device.manipulated.reference or "Unknown Device"

            devices.append({
                "action": action_str,
                "manipulated": manipulated_str
            })
        return devices

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