from fhir.resources.medication import Medication as FhirMedication
from typing import Optional, List, Dict

from resources.core.types import AppCodeableConcept

class AppMedication:
   def __init__(self, raw_json_data: dict):
      self.resource = FhirMedication(**raw_json_data)

   @property
   def id(self) -> str:
      return self.resource.id

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

   def to_prompt_string(self) -> Optional[str]:
      name = self.code_text
      details = self.code_details

      if not name and not details:
         return None
      
      display_name = name if name else ""
      
      codes_str = ""
      if details:
         code_items = [f"{d['system']}: {d['code']}" for d in details]
         codes_str = f" ({', '.join(code_items)})"
      
      return f"{display_name}{codes_str}"