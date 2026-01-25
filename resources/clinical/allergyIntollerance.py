from fhir.resources.allergyintolerance import AllergyIntolerance as FhirAllergyIntolerance
from typing import Optional, Dict

class AppAllergyIntolerance:
    
    # Mapping SNOMED CT codes to specific readable string representations of the specific allergies
    SNOMED_MAPPING: Dict[str, str] = {
        "425525006": "Allergy to dairy product",
        "91930004": "Allergy to eggs",
        "227037002": "Allergy to fish",
        "91935009": "Allergy to peanuts",
        "294659004": "Allergy to wheat",
        "300913006": "Shellfish allergy",
        "300916003": "Latex allergy"
    }

    # Initialize the FHIR resource
    def __init__(self, raw_json_data: dict):
        self.resource = FhirAllergyIntolerance(**raw_json_data)


    @property
    def id(self) -> str:
        return self.resource.id


    # Returns the clinical status (e.g., active, inactive, resolved)
    @property
    def clinical_status(self) -> str:
        if self.resource.clinicalStatus and self.resource.clinicalStatus.coding:
            return self.resource.clinicalStatus.coding[0].code
        return "unknown"


    # Returns the verification status (e.g., unconfirmed, confirmed, refuted)
    @property
    def verification_status(self) -> str:
        if self.resource.verificationStatus and self.resource.verificationStatus.coding:
            return self.resource.verificationStatus.coding[0].code
        return "unknown"


    # Returns the category (food, medication, environment, etc.) as a string
    @property
    def category(self) -> str:
        if self.resource.category:
            # Category is a list in FHIR, usually we take the first one
            return self.resource.category[0]
        return "unknown"


    # Returns the criticality (low, high, unable-to-assess)
    @property
    def criticality(self) -> str:
        return self.resource.criticality or "unknown"


    # Internal logic to resolve the specific name of the allergy based on SNOMED codes
    def _get_display_name(self) -> str:
        if not self.resource.code:
            return "Unknown Allergy"

        # 1. Try to match specific SNOMED codes from our mapping
        if self.resource.code.coding:
            for coding in self.resource.code.coding:
                # We check if the code exists in our specific mapping
                if coding.code in self.SNOMED_MAPPING:
                    return self.SNOMED_MAPPING[coding.code]

        # 2. If not found in mapping, return the text provided in the resource
        if self.resource.code.text:
            return self.resource.code.text

        # 3. Fallback: return the display of the first coding found
        if self.resource.code.coding and self.resource.code.coding[0].display:
            return self.resource.code.coding[0].display

        return "Unnamed Allergy"


    # Returns the type: 'allergy' or 'intolerance'
    @property
    def type(self) -> Optional[str]:
        return self.resource.type


    # Represents the date and/or time of the last known occurrence of a reaction event
    @property
    def lastOccurrence(self) -> Optional[datetime]:
        return self.resource.lastOccurrence


    # The recordedDate represents when this particular record was created in the system, which is often the current time
    @property
    def recordedDate(self) -> Optional[datetime]:
        return self.resource.recordedDate
    """
        Returns a list of reactions associated with this allergy.
        Structure:
        [
            {
                "substance": str,
                "manifestation": str (joined by comma if multiple),
                "severity": str,
                "exposureRoute": str
            },
            ...
        ]
    """
    @property
    def reactions(self) -> List[Dict[str, any]]:        
        if not self.resource.reaction:
            return []

        formatted_reactions = []
        
        for reaction in self.resource.reaction:
            # 1. Substance
            substance_str = self._get_concept_display(reaction.substance)
            
            # 2. Manifestation (FHIR allows multiple manifestations per reaction)
            manifestations = []
            if reaction.manifestation:
                for man in reaction.manifestation:
                    manifestations.append(self._get_concept_display(man) or "Unknown")
            manifestation_str = ", ".join(manifestations)

            # 3. Severity (Simple code: mild | moderate | severe)
            severity_str = reaction.severity

            # 4. Exposure Route
            route_str = self._get_concept_display(reaction.exposureRoute)

            formatted_reactions.append({
                "substance": substance_str,
                "manifestation": manifestation_str,
                "severity": severity_str,
                "exposureRoute": route_str
            })

        return formatted_reactions


    """
        Safely extracting the display from a FHIR CodeableConcept
        Priority: text -> coding.display -> None
    """
    def _get_concept_display(self, codeable_concept) -> Optional[str]:
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

    # UTIL METHODS
    def __eq__(self, other):
        if not isinstance(other, AppAllergyIntolerance):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    # Returns the type of allergy
    def __str__(self):
        return self._get_display_name()