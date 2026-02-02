'''
Script: types.py
Digital Health Systems and Applications - Project work 2025-2026
Description:
Helper class to handle HL7 FHIR CodeableConcept elements. It provides methods to
extract readable text, clean system names (e.g., SNOMED, LOINC), and bind
codes to Python Enums for easier logic handling.

Group: Carmine Vardaro, Marco Savastano, Francesco Ferrara.
'''

from enum import Enum
from typing import Optional, List, Dict, Type, TypeVar

from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding

T = TypeVar('T', bound=Enum)

class AppCodeableConcept:
    def __init__(self, source: CodeableConcept):
        self._source = source
        self.text: Optional[str] = getattr(source, "text", None)
        self.codings: List[Coding] = source.coding if source.coding else []

    @property
    def readable_value(self) -> Optional[str]:
        """
        Returns the most human-readable text available:
        1. The 'text' field of the CodeableConcept.
        2. The 'display' field of the first coding.
        """
        if self.text: 
            return self.text
        for coding in self.codings:
            if coding.display:
                return coding.display
        return None

    def _clean_system_name(self, uri: str) -> str:
        """
        Normalizes FHIR system URIs into readable standard names (e.g., SNOMED, LOINC).
        """
        uri_lower = uri.lower()
        if "snomed" in uri_lower: return "SNOMED"
        if "loinc" in uri_lower: return "LOINC"
        if "rxnorm" in uri_lower: return "RxNorm"
        if "icd-9" in uri_lower: return "ICD-9"
        if "icd-10" in uri_lower: return "ICD-10"
        if "unitsofmeasure" in uri_lower or "ucum" in uri_lower: return "UCUM"
        if "cvx" in uri_lower: return "CVX"
        if "ndc" in uri_lower: return "NDC"
        if "cpt" in uri_lower: return "CPT"
        return uri

    @property
    def coding_details(self) -> List[Dict[str, Optional[str]]]:
        """
        Extracts a list of coding details (system, code, display) for the concept.
        """
        results = []
        for coding in self.codings:
            if not coding.system or not coding.code:
                continue
            clean_sys = self._clean_system_name(coding.system)
            entry = {
                "system": clean_sys,
                "code": coding.code,
                "display": coding.display  # It can be None
            }
            results.append(entry)
        return results

    def bind_to(self, enum_class: Type[T]) -> Optional[T]: 
        """
        Attempts to map the codes in this concept to a provided Python Enum class.
        Returns the first matching Enum member or None.
        """
        if not self.codings:
            return None
        for coding in self.codings:
            if not coding.code: continue
            try:
                # Case-insensitive matching is safer for some systems
                return enum_class(coding.code.lower())
            except ValueError:
                continue
        return None