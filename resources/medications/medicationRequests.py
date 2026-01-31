from fhir.resources.medicationrequest import MedicationRequest as FhirMedicationRequest

from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime

from resources.core.types import AppCodeableConcept

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .app_medication import AppMedication 

class MedicationRequestStatus(str, Enum):
   ACTIVE = "active"
   ON_HOLD = "on-hold"
   CANCELLED = "cancelled"
   COMPLETED = "completed"
   ENTERED_IN_ERROR = "entered-in-error"
   STOPPED = "stopped"
   DRAFT = "draft"
   UNKNOWN = "unknown"

   @property
   def definition(self) -> str:
      #https://hl7.org/fhir/R4/valueset-medicationrequest-status.html
      definitions = {
         "active": "The prescription is 'actionable', but not all actions that are implied by it have occurred yet.",
         "on-hold": "	Actions implied by the prescription are to be temporarily halted, but are expected to continue later. May also be called 'suspended'.",
         "cancelled": "The prescription has been withdrawn before any administrations have occurred.",
         "completed": "All actions that are implied by the prescription have occurred.",
         "entered-in-error": "Some of the actions that are implied by the medication request may have occurred. For example, the medication may have been dispensed and the patient may have taken some of the medication. Clinical decision support systems should take this status into account",
         "stopped": "Actions implied by the prescription are to be permanently halted, before all of the administrations occurred. This should not be used if the original order was entered in error",
         "draft": "	The prescription is not yet 'actionable', e.g. it is a work in progress, requires sign-off, verification or needs to be run through decision support process.",
         "unknown": "The authoring/source system does not know which of the status values currently applies for this observation. Note: This concept is not to be used for 'other' - one of the listed statuses is presumed to apply, but the authoring/source system does not know which."
      }
      return definitions.get(self.value, "Definition not available.")

class MedicationRequestIntent(str, Enum):
   PROPOSAL = "proposal"
   PLAN = "plan"
   ORDER = "order"
   ORIGINAL_ORDER = "original-order"
   REFLEX_ORDER = "reflex-order"
   FILLER_ORDER = "filler-order"
   INSTANCE_ORDER = "instance-order"
   OPTION = "option"

   @property
   def definition(self) -> str:
      #https://hl7.org/fhir/R4/valueset-medicationrequest-intent.html
      definitions = {
         "proposal": "	The request is a suggestion made by someone/something that doesn't have an intention to ensure it occurs and without providing an authorization to act",
         "plan": "The request represents an intention to ensure something occurs without providing an authorization for others to act.",
         "order": "The request represents a request/demand and authorization for action",
         "original-order": "The request represents the original authorization for the medication request.",
         "reflex-order": "The request represents an automatically generated supplemental authorization for action based on a parent authorization together with initial results of the action taken against that parent authorization..",
         "filler-order": "	The request represents the view of an authorization instantiated by a fulfilling system representing the details of the fulfiller's intention to act upon a submitted order.",
         "instance-order": "The request represents an instance for the particular order, for example a medication administration record.",
         "option": "	The request represents a component or option for a RequestGroup that establishes timing, conditionality and/or other constraints among a set of requests."
      }
      return definitions.get(self.value, "Definition not available.")
   

class AppMedicationRequest:
   def __init__(self, raw_json_data: dict):
      self.resource = FhirMedicationRequest(**raw_json_data)

   @property
   def id(self) -> str:
      return self.resource.id

   @property
   def status(self) -> Optional[MedicationRequestStatus]:
      if not self.resource.status: 
         return None
      try: 
         return MedicationRequestStatus(self.resource.status)
      except ValueError: 
         return None

   @property
   def intent(self) -> Optional[MedicationRequestIntent]:
      if not self.resource.intent: 
         return None
      try: 
         return MedicationRequestIntent(self.resource.intent)
      except ValueError: 
         return None

   @property
   def authored_on(self) -> Optional[datetime]:
      return self.resource.authoredOn

   @property
   def medication_reference_id(self) -> Optional[str]:
      if self.resource.medicationReference and self.resource.medicationReference.reference:
         return self.resource.medicationReference.reference.split("/")[-1]
      return None

   @property
   def medication_concept_text(self) -> Optional[str]:
      if self.resource.medicationCodeableConcept:
         return AppCodeableConcept(self.resource.medicationCodeableConcept).readable_value
      return None

   @property
   def medication_concept_details(self) -> List[Dict[str, Optional[str]]]:
      if self.resource.medicationCodeableConcept:
         return AppCodeableConcept(self.resource.medicationCodeableConcept).coding_details
      return []

   @property
   def dosage_text(self) -> Optional[str]:
      """
      Versione 'Umanizzata'.
      - Rimuove decimali inutili (1.0 -> 1).
      - Traduce frequenze comuni (1/1d -> Once a day).
      - Ignora unità di misura della dose se mancanti/rotte.
      """
      if not self.resource.dosageInstruction:
         return None
      
      all_lines = []

      for dosage in self.resource.dosageInstruction:
         # 1. Priorità al testo libero
         if dosage.text:
               all_lines.append(dosage.text)
               continue 

         parts = []

         # --- A. DOSE (Solo il numero pulito) ---
         if dosage.doseAndRate:
               for dr in dosage.doseAndRate:
                  if dr.doseQuantity and dr.doseQuantity.value is not None:
                     val = dr.doseQuantity.value
                     # Se è 1.0 diventa 1, se è 1.5 resta 1.5
                     val_str = str(int(val)) if val % 1 == 0 else str(val)
                     parts.append(val_str)
                     break 
         
         # --- B. TIMING (Traduzione in linguaggio naturale) ---
         if dosage.timing and dosage.timing.repeat:
               repeat = dosage.timing.repeat
               freq = repeat.frequency
               period = repeat.period
               unit = repeat.periodUnit # h, d, wk, mo

               if freq and period and unit:
                  # Logica di traduzione casi comuni
                  
                  # CASO 1: Giornaliero (Once a day)
                  # Copre: 1 volta per 1 giorno OPPURE 1 volta per 24 ore
                  if freq == 1 and ((period == 1 and unit == 'd') or (period == 24 and unit == 'h')):
                     parts.append("Once a day")
                  
                  # CASO 2: Due volte al giorno (Twice a day)
                  elif freq == 2 and ((period == 1 and unit == 'd') or (period == 24 and unit == 'h')):
                     parts.append("Twice a day")
                  
                  # CASO 3: Tre volte al giorno
                  elif freq == 3 and ((period == 1 and unit == 'd') or (period == 24 and unit == 'h')):
                     parts.append("3 times a day")
                  
                  # CASO 4: Generico "Every X hours" (es. ogni 8 ore)
                  elif freq == 1 and unit == 'h':
                        parts.append(f"Every {int(period)} hours")

                  # CASO 5: Fallback generico pulito (es. 3 times per week)
                  else:
                     unit_map = {'h': 'hour', 'd': 'day', 'wk': 'week', 'mo': 'month'}
                     u_str = unit_map.get(unit, unit)
                     if period > 1: u_str += "s" # Plurale
                     
                     parts.append(f"{freq} times per {int(period)} {u_str}")

         # Fallback codici (es. BID/TID)
         elif dosage.timing and dosage.timing.code:
               t_text = AppCodeableConcept(dosage.timing.code).readable_value
               if t_text: parts.append(t_text)

         # --- C. AL BISOGNO ---
         if dosage.asNeededBoolean:
               parts.append("As needed")
         
         if parts:
               all_lines.append(", ".join(parts))

      if not all_lines:
         return None
         
      return "; ".join(all_lines)


   def to_prompt_string(self, medication_map: Dict[str, 'AppMedication']) -> str:
      med_string = None

      ref_id = self.medication_reference_id
      if ref_id:
         if ref_id in medication_map:
            med_string = medication_map[ref_id].to_prompt_string()
         else:
            med_string = f"Medication/{ref_id} (Details missing)"      
      elif self.medication_concept_text:
         name = self.medication_concept_text
         details = self.medication_concept_details
         codes_str = ""
         if details:
            code_items = [f"{d['system']}: {d['code']}" for d in details]
            codes_str = f" ({', '.join(code_items)})"
         med_string = f"{name}{codes_str}"

      if not med_string:
         return ""

      meta_parts = []
      if self.status:
         meta_parts.append(self.status.value.capitalize())
      # Intent è spesso ridondante se è "Order", lo mettiamo solo se particolare
      # if self.intent and self.intent != MedicationRequestIntent.ORDER:
      #    meta_parts.append(self.intent.value)
      if self.authored_on:
         meta_parts.append(f"[{self.authored_on.strftime('%Y-%m-%d')}]")

      meta_str = f" ({', '.join(meta_parts)})" if meta_parts else ""

      dosage_str = ""
      d_text = self.dosage_text
      if d_text:
         dosage_str = f"\n  Dosage: {d_text}"

      return f"- {med_string}{meta_str}{dosage_str}"
