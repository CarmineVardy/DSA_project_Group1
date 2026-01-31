from enum import Enum
from typing import Optional, List, Dict, Type, TypeVar, Any

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
        if self.text: 
            return self.text
        for coding in self.codings:
            if coding.display:
                return coding.display
        return None

    def _clean_system_name(self, uri: str) -> str:
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
        if not self.codings:
            return None
        for coding in self.codings:
            if not coding.code: continue
            try:
                return enum_class(coding.code.lower())
            except ValueError:
                continue
        return None
