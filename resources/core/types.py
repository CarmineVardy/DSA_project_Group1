from enum import Enum
from typing import Optional, Type, TypeVar, List, Dict, Any
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding

# Generic type for Enums
T = TypeVar('T', bound=Enum)

class AppCodeableConcept:
    """
    Internal Helper Wrapper. 
    It handles the complexity of FHIR CodeableConcept:
    - 0..1 text
    - 0..* codings (Coding)
    """
    def __init__(self, source: CodeableConcept):
        self._source = source
        self.text: Optional[str] = getattr(source, "text", None)
        self.codings: List[Coding] = source.coding if source.coding else []

    @property
    def readable_value(self) -> Optional[str]:
        #Priority: Text > Display (first) > Code (first) > Unknown
        if self.text: return self.text
        if self.codings:
            first = self.codings[0]
            if first.display: return first.display
            if first.code: return f"Code: {first.code}"
        return None

    @property
    def all_readable_values(self) -> List[str]:
        #No only one description but all we have (text and display for each coding)
        values = []
        if self.text:
            values.append(self.text)

        for coding in self.codings:
            if coding.display:
                values.append(coding.display)
            elif coding.code:
                values.append(f"Code:{coding.code}")
        return list(dict.fromkeys(values))


    @property
    def coding_count(self) -> int:
        return len(self.codings)

    @property
    def has_text(self) -> bool:
        return bool(self.text)

    @property
    def all_codings_details(self) -> List[Dict[str, str]]:
        """
        Returns a clean list of dictionaries for all codings.
        You get a list like:
        [
          {'system': 'http://snomed...', 'code': '123', 'display': 'Flu'},
          {'system': 'local-db', 'code': 'XYZ', 'display': None}
        ]
        """
        results = []
        for coding in self.codings:
            results.append({
                "system": coding.system or "No System",
                "version": coding.version or "No Version",
                "code": coding.code or "No Code",
                "display": coding.display or "No Display"
            })
        return results

    def bind_to(self, enum_class: Type[T]) -> Optional[T]: 
        if not self.codings:
            return None
        for coding in self.codings:
            if not coding.code: continue
            try:
                return enum_class(coding.code)
            except ValueError:
                continue
        return None
