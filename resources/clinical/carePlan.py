from fhir.resources.careplan import CarePlan as FhirCarePlan
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference
from typing import Optional, List, Dict, Union, Any
from datetime import datetime

class AppCarePlan:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirCarePlan(**raw_json_data)

    @property
    def id(self) -> str:
        return self.resource.id


    # draft | active | on-hold | revoked | completed | entered-in-error | unknown
    @property
    def status(self) -> str:
        return self.resource.status


    # proposal | plan | order | option
    @property
    def intent(self) -> str:
        return self.resource.intent

    # Human-friendly name for the CarePlan
    @property
    def title(self) -> str:
        return self.resource.title or "Untitled Care Plan"


    # Summary of the scope and nature of the plan
    @property
    def description(self) -> str:
        return self.resource.description or ""


    # Date record was first created
    @property
    def created(self) -> Optional[datetime]:
        return self.resource.created


    # Time period plan covers. Returns dict with start/end
    @property
    def period(self) -> Optional[Dict[str, datetime]]:
        if self.resource.period:
            return {
                "start": self.resource.period.start,
                "end": self.resource.period.end
            }
        return None


    # Type of plan (e.g. "weight loss", "post-op")
    @property
    def category(self) -> List[str]:
        if not self.resource.category:
            return []
        return [self._get_concept_display(cat) for cat in self.resource.category]


    # Health issues this plan addresses (usually references to Conditions)
    @property
    def addresses(self) -> List[str]:

        if not self.resource.addresses:
            return []
        return [self._get_reference_display(ref) for ref in self.resource.addresses]


    # Information considered as part of the plan (e.g. DiagnosticReports)
    @property
    def supportingInfo(self) -> List[str]:
        if not self.resource.supportingInfo:
            return []
        return [self._get_reference_display(ref) for ref in self.resource.supportingInfo]


    # Desired outcomes of this plan
    @property
    def goals(self) -> List[str]:
        if not self.resource.goal:
            return []
        return [self._get_reference_display(ref) for ref in self.resource.goal]


    """
        Action to occur as part of the plan.
        Returns a structured list including:
         - performedActivity (outcomes)
         - progress (notes on status)
         - detail (the planned action itself)
    """
    @property
    def activity(self) -> List[Dict[str, Any]]:
        if not self.resource.activity:
            return []

        activities_data = []

        for act in self.resource.activity:
            # 1. Performed Activity / Outcome
            # In FHIR R4 = 'outcomeReference' or 'outcomeCodeableConcept'
            performed_list = []
            if act.outcomeReference:
                performed_list.extend([self._get_reference_display(ref) for ref in act.outcomeReference])
            if act.outcomeCodeableConcept:
                performed_list.extend([self._get_concept_display(code) for code in act.outcomeCodeableConcept])
            
            # 2. Progress
            # act.progress is a list of Annotations
            progress_list = []
            if act.progress:
                for note in act.progress:
                    if note.text:
                        # You might also want note.time or note.authorString here
                        progress_list.append(note.text)

            # 3. Detail
            # This describes the intention or what is to be done
            detail_dict = {}
            if act.detail:
                detail_dict = {
                    "kind": act.detail.kind,  # e.g., Appointment, MedicationRequest
                    "code": self._get_concept_display(act.detail.code),
                    "status": act.detail.status,
                    "reason": self._get_concept_display(act.detail.reasonCode and act.detail.reasonCode[0]),
                    "scheduledString": act.detail.scheduledString, # Simple string representation if available
                    "location": self._get_concept_display(act.detail.location) if act.detail.location else None
                }
            elif act.reference:
                # Fallback if 'detail' is not used but 'reference' is
                detail_dict = {
                    "reference": self._get_reference_display(act.reference),
                    "status": "referred"
                }

            activities_data.append({
                "performedActivity": performed_list,
                "progress": progress_list,
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

    """
        Helper to extract text from a Reference.
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
        return f"{self.title} ({self.status})"