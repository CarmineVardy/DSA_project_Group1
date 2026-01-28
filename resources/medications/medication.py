from fhir.resources.medication import Medication as FhirMedication
from fhir.resources.codeableconcept import CodeableConcept
from typing import Optional, List, Dict, Any

class AppMedication:
    
    UC1_SELECTED = [
        "10 ML Alfentanil 0.5 MG/ML Injection",
        "10 ML Fentanyl 0.05 MG/ML Injection",
        "10 ML Furosemide 10 MG/ML Injection",
        "100 ML Propofol 10 MG/ML Injection",
        "2 ML Ondansetron 2 MG/ML Injection",
        "5 ML SUFentanil 0.05 MG/ML Injection",
        "Calcium Carbonate 1250 MG / Cholecalciferol 1000 UNT / Vitamin K 0.4 MG Chewable Tablet",
        "Cisplatin 50 MG Injection",
        "Etoposide 100 MG Injection",
        "PACLitaxel 100 MG Injection",
        "remifentanil 2 MG Injection"
    ]

    UC2_SELECTED = [
        "10 ML Alfentanil 0.5 MG/ML Injection",
        "10 ML Fentanyl 0.05 MG/ML Injection",
        "10 ML Furosemide 10 MG/ML Injection",
        "100 ML Propofol 10 MG/ML Injection",
        "2 ML Ondansetron 2 MG/ML Injection",
        "5 ML SUFentanil 0.05 MG/ML Injection",
        "Calcium Carbonate 1250 MG / Cholecalciferol 1000 UNT / Vitamin K 0.4 MG Chewable Tablet",
        "Cisplatin 50 MG Injection",
        "Diazepam 5 MG/ML Injectable Solution",
        "Etoposide 100 MG Injection",
        "Isoflurane 999 MG/ML Inhalant Solution",
        "Midazolam 1 MG/ML Injectable Solution",
        "PACLitaxel 100 MG Injection",
        "Rocuronium bromide 10 MG/ML Injectable Solution",
        "desflurane 1000 MG/ML Inhalation Solution",
        "remifentanil 2 MG Injection"
    ]

    SNOMED_MAPPING: Dict[str, str] = {
        "10 ML Alfentanil 0.5 MG/ML Injection": "",
        "10 ML Fentanyl 0.05 MG/ML Injection": "",
        "10 ML Furosemide 10 MG/ML Injection": "",
        "100 ML Propofol 10 MG/ML Injection": "",
        "2 ML Ondansetron 2 MG/ML Injection": "",
        "5 ML SUFentanil 0.05 MG/ML Injection": "",
        "Calcium Carbonate 1250 MG / Cholecalciferol 1000 UNT / Vitamin K 0.4 MG Chewable Tablet": "",
        "Cisplatin 50 MG Injection": "",
        "Etoposide 100 MG Injection": "",
        "PACLitaxel 100 MG Injection": "",
        "remifentanil 2 MG Injection": "",
        "Diazepam 5 MG/ML Injectable Solution": "",
        "Isoflurane 999 MG/ML Inhalant Solution": "",
        "Midazolam 1 MG/ML Injectable Solution": "",
        "Rocuronium bromide 10 MG/ML Injectable Solution": "",
        "desflurane 1000 MG/ML Inhalation Solution": ""
    }

    def __init__(self, raw_json_data: dict):
        self.raw = raw_json_data
        try:
            self.resource = FhirMedication(**raw_json_data)
        except Exception:
            self.resource = None

    def get_snomed_code(self, medication_name: str) -> Optional[str]:
        return self.SNOMED_MAPPING.get(medication_name)

    def check_is_selected(self, use_case: str) -> bool:
        current_name = self.code.strip()
        target_list = []

        if use_case.lower() == "uc1":
            target_list = self.UC1_SELECTED
        elif use_case.lower() == "uc2":
            target_list = self.UC2_SELECTED
        else:
            return False

        for item in target_list:
            if item.lower() in current_name.lower():
                return True
        return False

    @property
    def id(self) -> str:
        return self.raw.get('id')

    @property
    def status(self) -> str:
        return self.resource.status if self.resource else self.raw.get('status', 'unknown')

    @property
    def code(self) -> str:
        if self.resource:
            return self._get_concept_display(self.resource.code) or "Unknown Medication"
        return self._get_concept_display_raw(self.raw.get('code')) or "Unknown Medication"

    @property
    def meta(self) -> Dict[str, Any]:
        return self.raw.get('meta', {})

    @property
    def resourceType(self) -> str:
        return self.raw.get('resourceType', 'Medication')

    def _get_concept_display(self, codeable_concept: Optional[CodeableConcept]) -> Optional[str]:
        if not codeable_concept: return None
        if codeable_concept.text: return codeable_concept.text
        if codeable_concept.coding:
            for coding in codeable_concept.coding:
                if coding.display: return coding.display
        return None

    def _get_concept_display_raw(self, raw_concept: dict) -> Optional[str]:
        if not raw_concept: return None
        if raw_concept.get('text'): return raw_concept['text']
        codings = raw_concept.get('coding', [])
        for coding in codings:
            if coding.get('display'): return coding['display']
        return None

    def __eq__(self, other):
        if not isinstance(other, AppMedication): return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        lines = [
            f"ID: {self.id}",
            f"Code: {self.code}",
            f"Status: {self.status}",
            f"Type: {self.resourceType}"
        ]
        return "\n".join(lines)