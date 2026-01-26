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


    # Reason why the immunization was not done (if status is not-done)
    @property
    def statusReason(self) -> Optional[str]:
        return self._get_concept_display(self.resource.statusReason)


    # Vaccine product administered (e.g. 'Influenza, seasonal')
    @property
    def vaccineCode(self) -> str:
        return self._get_concept_display(self.resource.vaccineCode) or "Unknown Vaccine"

    # --- SPECIFIC DETAILS ---
    # Lot number of the vaccine product
    @property
    def lotNumber(self) -> Optional[str]:
        return self.resource.lotNumber

    # Date vaccine lot expires
    @property
    def expirationDate(self) -> Optional[date]:
        return self.resource.expirationDate

    # Body site where vaccine was administered (e.g. 'Left arm')
    @property
    def site(self) -> Optional[str]:
        return self._get_concept_display(self.resource.site)

    # How vaccine entered body (e.g. 'Intramuscular injection')
    @property
    def route(self) -> Optional[str]:
        return self._get_concept_display(self.resource.route)


    # Returns datetime object if specific time is known, otherwise the string representation
    @property
    def occurrence(self) -> Union[datetime, str, None]:
        if self.resource.occurrenceDateTime:
            return self.resource.occurrenceDateTime
        if self.resource.occurrenceString:
            return self.resource.occurrenceString
        return None

    @property
    def occurrence_display(self) -> str:
        """
        Helper for UI display.
        """
        val = self.occurrence
        if isinstance(val, (datetime, date)):
            return val.strftime("%Y-%m-%d")
        return str(val) if val else "Unknown Date"

    @property
    def doseQuantity(self) -> Optional[str]:
        """
        Amount of vaccine administered. Returns formatted string 'Value Unit'.
        """
        if self.resource.doseQuantity:
            value = self.resource.doseQuantity.value
            unit = self.resource.doseQuantity.unit or self.resource.doseQuantity.code or ""
            return f"{value} {unit}".strip()
        return None

    @property
    def isSubpotent(self) -> bool:
        """
        True if dose is considered subpotent (less than recommended).
        """
        return self.resource.isSubpotent is True

    # Details of a reaction that follows immunization
    @property
    def reactions(self) -> List[Dict[str, Any]]:
        if not self.resource.reaction:
            return []

        results = []
        for react in self.resource.reaction:
            results.append({
                "date": react.date,
                "reported": react.reported, # Boolean: True -> self-reported
                "detail": react.detail.display if react.detail else "Unknown Reaction"
            })
        return results

    # --- PROTOCOL APPLIED ---
    # The protocol (set of recommendations) followed by the provider
    @property
    def protocolApplied(self) -> List[Dict[str, Any]]:
        if not self.resource.protocolApplied:
            return []

        protocols = []
        for proto in self.resource.protocolApplied:
            # Target Disease: list of concepts
            diseases = []
            if proto.targetDisease:
                diseases = [self._get_concept_display(d) for d in proto.targetDisease]
            
            # Handle Choice types for Dose Number and Series Doses (PositiveInt OR String)
            dose_num = getattr(proto, "doseNumberPositiveInt", None) or getattr(proto, "doseNumberString", None)
            series_doses = getattr(proto, "seriesDosesPositiveInt", None) or getattr(proto, "seriesDosesString", None)

            protocols.append({
                "series": proto.series, # Name of the series (e.g. "2-dose series")
                "targetDisease": ", ".join(filter(None, diseases)),
                "doseNumber": dose_num, # e.g. 1
                "seriesDoses": series_doses # e.g. 2
            })
        return protocols

    # --- UTIL METHODS ---
    # Helper to safely extract display text from a FHIR CodeableConcept.
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