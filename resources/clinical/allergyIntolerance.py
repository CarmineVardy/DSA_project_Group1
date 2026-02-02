'''
Script: allergyIntolerance.py
Digital Health Systems and Applications - Project work 2025-2026
Description:
Wrapper class for the HL7 FHIR AllergyIntolerance resource. It standardizes the representation
of allergy information, including clinical status, verification status, categories, criticality,
and coding details, for use in the CDSS context.

Group: Carmine Vardaro, Marco Savastano, Francesco Ferrara.
'''

from fhir.resources.allergyintolerance import AllergyIntolerance as FhirAllergyIntolerance

from enum import Enum
from typing import Optional, List, Dict

from resources.core.types import AppCodeableConcept

class AllergyClinicalStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESOLVED = "resolved"

    @property
    def definition(self) -> str:
        #https://hl7.org/fhir/R4/valueset-allergyintolerance-clinical.html
        definitions = {
            "active": "The subject is currently experiencing, or is at risk of, a reaction to the identified substance.",
            "inactive": "The subject is no longer at risk of a reaction to the identified substance.",
            "resolved": "A reaction to the identified substance has been clinically reassessed by testing or re-exposure and is considered no longer to be present. Re-exposure could be accidental, unplanned, or outside of any clinical setting."
        }
        return definitions.get(self.value, "Definition not available.")


class AllergyVerificationStatus(str, Enum):
    UNCONFIRMED = "unconfirmed"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    ENTERED_IN_ERROR = "entered-in-error"

    @property
    def definition(self) -> str:
        #https://hl7.org/fhir/R4/valueset-allergyintolerance-verification.html
        definitions = {
            "unconfirmed": "A low level of certainty about the propensity for a reaction to the identified substance.",
            "confirmed": "A high level of certainty about the propensity for a reaction to the identified substance, which may include clinical evidence by testing or rechallenge.",
            "refuted": "A propensity for a reaction to the identified substance has been disputed or disproven with a sufficient level of clinical certainty to justify invalidating the assertion. This might or might not include testing or rechallenge.",
            "entered-in-error": "The statement was entered in error and is not valid."
        }
        return definitions.get(self.value, "Definition not available.")


class AllergyType(str, Enum):
    ALLERGY = "allergy"
    INTOLERANCE = "intolerance"

    @property
    def definition(self) -> str:
        #https://hl7.org/fhir/R4/valueset-allergy-intolerance-type.html
        definitions = {
            "allergy": 'A propensity for hypersensitive reaction(s) to a substance. These reactions are most typically type I hypersensitivity, plus other "allergy-like" reactions, including pseudoallergy.',
            "intolerance": 'A propensity for adverse reactions to a substance that is not judged to be allergic or "allergy-like". These reactions are typically (but not necessarily) non-immune. They are to some degree idiosyncratic and/or patient-specific (i.e. are not a reaction that is expected to occur with most or all patients given similar circumstances).'
        }
        return definitions.get(self.value, "Definition not available.")


class AllergyCategory(str, Enum):
    FOOD = "food"
    MEDICATION = "medication"
    ENVIRONMENT = "environment"
    BIOLOGIC = "biologic"

    @property
    def definition(self) -> str:
        #https://hl7.org/fhir/R4/valueset-allergy-intolerance-category.html
        definitions = {
            "food": "Any substance consumed to provide nutritional support for the body.",
            "medication": "Substances administered to achieve a physiological effect.",
            "environment": "Any substances that are encountered in the environment, including any substance not already classified as food, medication, or biologic.",
            "biologic": "A preparation that is synthesized from living organisms or their products, especially a human or animal protein, such as a hormone or antitoxin, that is used as a diagnostic, preventive, or therapeutic agent. Examples of biologic medications include: vaccines; allergenic extracts, which are used for both diagnosis and treatment (for example, allergy shots); gene therapies; cellular therapies. There are other biologic products, such as tissues, which are not typically associated with allergies."
        }
        return definitions.get(self.value, "Definition not available.")

class AllergyCriticality(str, Enum):
    LOW = "low"
    HIGH = "high"
    UNABLE_TO_ASSESS = "unable-to-assess"

    @property
    def definition(self) -> str:
        #https://hl7.org/fhir/R4/valueset-allergyintolerance-verification.html
        definitions = {
            "low": "Worst case result of a future exposure is not assessed to be life-threatening or having high potential for organ system failure.",
            "high": "Worst case result of a future exposure is assessed to be life-threatening or having high potential for organ system failure.",
            "unable-to-assess": "Unable to assess the worst case result of a future exposure."
        }
        return definitions.get(self.value, "Definition not available.")

class AppAllergyIntolerance:

    def __init__(self, raw_json_data: dict):
        self.resource = FhirAllergyIntolerance(**raw_json_data)

    @property
    def id(self):
        return self.resource.id

    @property
    def clinical_status(self) -> Optional[AllergyClinicalStatus]:
        if not self.resource.clinicalStatus:
            return None    
        return AppCodeableConcept(self.resource.clinicalStatus).bind_to(AllergyClinicalStatus)
    
    @property
    def verification_status(self) -> Optional[AllergyVerificationStatus]:
        if not self.resource.verificationStatus:
            return None 
        return AppCodeableConcept(self.resource.verificationStatus).bind_to(AllergyVerificationStatus)

    @property
    def type(self) -> Optional[AllergyType]:
        if not self.resource.type: 
            return None
        try: 
            return AllergyType(self.resource.type)
        except ValueError: 
            return None

    @property
    def category(self) -> Optional[AllergyCategory]:
        if not self.resource.category:
            return None
        for cat_code in self.resource.category:
            try:
                return AllergyCategory(cat_code)
            except ValueError:
                continue
        return None

    @property
    def criticality(self) -> Optional[AllergyCriticality]:
        if not self.resource.criticality: 
            return None
        try: 
            return AllergyCriticality(self.resource.criticality)
        except ValueError: 
            return None

    @property
    def code_text(self) -> Optional[str]:
        if not self.resource.code: 
            return None
        return AppCodeableConcept(self.resource.code).readable_value

    @property
    def code_details(self) -> List[Dict[str, Optional[str]]]:
        if not self.resource.code: 
            return []    
        return AppCodeableConcept(self.resource.code).coding_details


    def to_prompt_string(self) -> str:
        name = self.code_text or "Unknown Substance"
        
        # Meta-info (Category and Type)
        meta_parts = []
        if self.category:
            meta_parts.append(self.category.value.capitalize())
        if self.type:
            meta_parts.append(self.type.value.capitalize())
        
        meta_str = f" ({' '.join(meta_parts)})" if meta_parts else ""

        # Verification Status Management: Mention ONLY if "Unconfirmed"
        ver_str = ""
        if self.verification_status == AllergyVerificationStatus.UNCONFIRMED:
            ver_str = " (Unconfirmed)"

        # Criticality Management
        crit_str = ""
        if self.criticality == AllergyCriticality.HIGH:
            crit_str = " [CRITICAL/HIGH RISK]" 
        elif self.criticality:
            crit_str = f" [CRITICAL {self.criticality.value}]"

        # Code Management (Clean syntax)
        code_str = ""
        if self.code_details:
            code_parts = []
            for c in self.code_details:
                # Direct syntax formatting
                code_parts.append(f"[{c['system']}: {c['code']}]")
            
            if code_parts:
                code_str = " " + " ".join(code_parts)

        return f"- {name}{meta_str}{ver_str}{crit_str}{code_str}"