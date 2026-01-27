from fhir.resources.allergyintolerance import AllergyIntolerance as FhirAllergyIntolerance
from typing import Optional, List, Dict
from datetime import datetime

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
        self.raw = raw_json_data
        try:
            self.resource = FhirAllergyIntolerance(**raw_json_data)
        except Exception:
            # Fallback if validation fails totally
            self.resource = None

    @property
    def id(self) -> str:
        return self.raw.get('id')

    # Returns the clinical status (e.g., active, inactive, resolved)
    @property
    def clinical_status(self) -> str:
        # Check resource first
        if self.resource and self.resource.clinicalStatus and self.resource.clinicalStatus.coding:
            return self.resource.clinicalStatus.coding[0].code
        
        # Raw fallback
        cs = self.raw.get('clinicalStatus')
        if cs and 'coding' in cs:
            return cs['coding'][0].get('code', 'unknown')
        return "unknown"

    # Returns the verification status (e.g., unconfirmed, confirmed, refuted)
    @property
    def verification_status(self) -> str:
        if self.resource and self.resource.verificationStatus and self.resource.verificationStatus.coding:
            return self.resource.verificationStatus.coding[0].code
        
        # Raw fallback
        vs = self.raw.get('verificationStatus')
        if vs and 'coding' in vs:
            return vs['coding'][0].get('code', 'unknown')
        return "unknown"

    # Returns the category (food, medication, environment, etc.) as a string
    @property
    def category(self) -> str:
        if self.resource and self.resource.category:
            return self.resource.category[0]
        
        cats = self.raw.get('category', [])
        if cats:
            return cats[0]
        return "unknown"

    # Returns the criticality (low, high, unable-to-assess)
    @property
    def criticality(self) -> str:
        if self.resource:
            return self.resource.criticality or "unknown"
        return self.raw.get('criticality', 'unknown')

    # Internal logic to resolve the specific name of the allergy based on SNOMED codes
    def _get_display_name(self) -> str:
        code_data = self.raw.get('code')
        if not code_data:
            return "Unknown Allergy"

        # 1. Try to match specific SNOMED codes from our mapping
        if 'coding' in code_data:
            for coding in code_data['coding']:
                if coding.get('code') in self.SNOMED_MAPPING:
                    return self.SNOMED_MAPPING[coding['code']]

        # 2. If not found in mapping, return the text provided in the resource
        if 'text' in code_data:
            return code_data['text']

        # 3. Fallback: return the display of the first coding found
        if 'coding' in code_data and code_data['coding']:
            return code_data['coding'][0].get('display', "Unnamed Allergy")

        return "Unnamed Allergy"

    # Returns the type: 'allergy' or 'intolerance'
    @property
    def type(self) -> Optional[str]:
        if self.resource:
            return self.resource.type
        return self.raw.get('type')


    # The recordedDate represents when this particular record was created in the system, which is often the current time
    @property
    def recordedDate(self) -> Optional[datetime]:
        if self.resource:
            return self.resource.recordedDate
        return self.raw.get('recordedDate')


    """
        Safely extracting the display from a FHIR CodeableConcept
        Priority: text -> coding.display -> None
    """
    def _get_concept_display_raw(self, raw_concept: dict) -> Optional[str]:
        if not raw_concept:
            return None
        if raw_concept.get('text'):
            return raw_concept['text']
        if raw_concept.get('coding'):
            for coding in raw_concept['coding']:
                if coding.get('display'):
                    return coding['display']
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