from fhir.resources.careplan import CarePlan as FhirCarePlan
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference

from typing import Optional, List, Dict, Union, Any
from datetime import datetime

class AppCarePlan:
    def __init__(self, raw_json_data: dict):
        self.raw = raw_json_data
        
        # 1. Sanitize data to prevent validation crashes (e.g. Invalid JSON in addresses)
        safe_data = raw_json_data.copy()
        
        # We remove fields that often cause version mismatch errors or strict validation failures
        keys_to_remove = ['addresses', 'goal', 'supportingInfo']
        for key in keys_to_remove:
            if key in safe_data:
                del safe_data[key]

        # 2. Try to initialize the strict FHIR resource with the safe data
        try:
            self.resource = FhirCarePlan(**safe_data)
        except Exception:
            self.resource = None

    @property
    def id(self) -> str:
        return self.raw.get('id')

    # draft | active | on-hold | revoked | completed | entered-in-error | unknown
    @property
    def status(self) -> str:
        return self.raw.get('status', 'unknown')

    # proposal | plan | order | option
    @property
    def intent(self) -> str:
        return self.raw.get('intent', 'unknown')


    # Time period plan covers. Returns dict with start/end
    @property
    def period(self) -> Optional[Dict[str, datetime]]:
        if self.resource and self.resource.period:
            return {
                "start": self.resource.period.start,
                "end": self.resource.period.end
            }
        
        # Raw fallback
        p = self.raw.get('period')
        if p:
             return {"start": p.get('start'), "end": p.get('end')}
        return None

    # Type of plan (e.g. "weight loss", "post-op")
    @property
    def category(self) -> List[str]:
        # Use resource if available
        if self.resource and self.resource.category:
            # Filter out None values to prevent "sequence item 0: expected str, NoneType found"
            return [
                disp for cat in self.resource.category 
                if (disp := self._get_concept_display(cat)) is not None
            ]
        
        # Fallback to raw
        raw_cats = self.raw.get('category', [])
        results = []
        for cat in raw_cats:
            disp = self._get_concept_display_raw(cat)
            if disp:
                results.append(disp)
        return results

    # Health issues this plan addresses (usually references to Conditions)
    @property
    def addresses(self) -> List[str]:
        # Always use raw because this field caused the "Invalid JSON" crash
        refs = self.raw.get('addresses', [])
        results = []
        for ref in refs:
            # Handle if ref is a dict (standard) or string (invalid server response)
            if isinstance(ref, dict):
                val = ref.get('display') or ref.get('reference')
                if val: 
                    results.append(val)
                else:
                    results.append("Unknown")
            elif isinstance(ref, str):
                results.append(ref)
        return results


    """
        Action to occur as part of the plan.
        Returns a structured list including:
         - performedActivity (outcomes)
         - progress (notes on status)
         - detail (the planned action itself)
    """
    @property
    def activity(self) -> List[Dict[str, Any]]:
        # Strictly use raw because R4 activity structure is complex
        raw_activities = self.raw.get('activity', [])
        activities_data = []

        for act in raw_activities:
            # 1. Performed Activity / Outcome
            performed_list = []
            
            # outcomeReference
            for ref in act.get('outcomeReference', []):
                val = ref.get('display') or ref.get('reference')
                if val: performed_list.append(val)
            
            # outcomeCodeableConcept
            for code in act.get('outcomeCodeableConcept', []):
                val = self._get_concept_display_raw(code)
                if val: performed_list.append(val)

            # 3. Detail
            detail = act.get('detail', {})
            detail_dict = {}
            if detail:
                # Safely get code
                code_val = self._get_concept_display_raw(detail.get('code'))
                
                # Safely get reason
                reasons = detail.get('reasonCode', [])
                reason_val = None
                if reasons and len(reasons) > 0:
                    reason_val = self._get_concept_display_raw(reasons[0])

                detail_dict = {
                    "kind": detail.get('kind'),
                    "code": code_val,
                    "status": detail.get('status'),
                    "reason": reason_val,
                    "scheduledString": detail.get('scheduledString')
                }
            elif act.get('reference'):
                ref = act['reference']
                detail_dict = {
                    "reference": ref.get('display') or ref.get('reference'),
                    "status": "referred"
                }

            activities_data.append({
                "performedActivity": performed_list,
                "detail": detail_dict
            })

        return activities_data

    # --- UTIL METHODS ---
    """
        Helper to safely extract display text from a FHIR CodeableConcept
        Priority: text -> coding.display -> None
    """
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

    def _get_concept_display_raw(self, raw_concept: dict) -> Optional[str]:
        if not raw_concept: return None
        if raw_concept.get('text'): return raw_concept['text']
        codings = raw_concept.get('coding', [])
        for coding in codings:
            if coding.get('display'): return coding['display']
        return None

    """
        Helper function to extract text from a Reference
        Priority: display -> reference string -> "Unknown Reference"
    """
    def _get_reference_display(self, reference: Optional[Reference]) -> str:
        if not reference:
            return "Unknown"
        if reference.display:
            return reference.display
        if reference.reference:
            return f"Ref: {reference.reference}"
        return "Unknown Reference"

    def _get_reference_display_raw(self, ref: dict) -> str:
        if not ref: return "Unknown"
        return ref.get('display') or ref.get('reference') or "Unknown Reference"

    def __eq__(self, other):
        if not isinstance(other, AppCarePlan):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    """
        Returns: Title (Status)
    """
    def __str__(self):        
        return f" {self.status}"