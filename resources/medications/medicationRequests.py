'''
Script: medicationRequests.py
Digital Health Systems and Applications - Project work 2025-2026
Description:
Wrapper class for the HL7 FHIR MedicationRequest resource. It handles prescription details,
statuses, intents, and provides a sophisticated logic to "humanize" dosage instructions
(converting complex FHIR timing structures into natural language) for the CDSS prompt.

Group: Carmine Vardaro, Marco Savastano, Francesco Ferrara.
'''

from fhir.resources.medicationrequest import MedicationRequest as FhirMedicationRequest

from enum import Enum
from typing import Optional, List, Dict, TYPE_CHECKING
from datetime import datetime

from resources.core.types import AppCodeableConcept

if TYPE_CHECKING:
    from .medication import AppMedication

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
         "on-hold": "Actions implied by the prescription are to be temporarily halted, but are expected to continue later. May also be called 'suspended'.",
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
        'Humanized' version of dosage instructions.
        - Removes useless decimals (1.0 -> 1).
        - Translates common frequencies (1/1d -> Once a day).
        - Ignores broken or missing unit measures.
        """
        if not self.resource.dosageInstruction:
            return None
        
        all_lines = []

        for dosage in self.resource.dosageInstruction:
            # 1. Priority to free text
            if dosage.text:
                all_lines.append(dosage.text)
                continue 

            parts = []

            # --- A. DOSE (Clean number only) ---
            if dosage.doseAndRate:
                for dr in dosage.doseAndRate:
                    if dr.doseQuantity and dr.doseQuantity.value is not None:
                        val = dr.doseQuantity.value
                        # If 1.0 becomes 1, if 1.5 stays 1.5
                        val_str = str(int(val)) if val % 1 == 0 else str(val)
                        parts.append(val_str)
                        break 
         
            # --- B. TIMING (Natural language translation) ---
            if dosage.timing and dosage.timing.repeat:
                repeat = dosage.timing.repeat
                freq = repeat.frequency
                period = repeat.period
                unit = repeat.periodUnit # h, d, wk, mo

                if freq and period and unit:
                    # Common cases translation logic
                    
                    # CASE 1: Daily (Once a day)
                    # Covers: 1 time per 1 day OR 1 time per 24 hours
                    if freq == 1 and ((period == 1 and unit == 'd') or (period == 24 and unit == 'h')):
                        parts.append("Once a day")
                    
                    # CASE 2: Twice a day
                    elif freq == 2 and ((period == 1 and unit == 'd') or (period == 24 and unit == 'h')):
                        parts.append("Twice a day")
                    
                    # CASE 3: Three times a day
                    elif freq == 3 and ((period == 1 and unit == 'd') or (period == 24 and unit == 'h')):
                        parts.append("3 times a day")
                    
                    # CASE 4: Generic "Every X hours" (e.g. every 8 hours)
                    elif freq == 1 and unit == 'h':
                         parts.append(f"Every {int(period)} hours")

                    # CASE 5: Clean generic fallback (e.g. 3 times per week)
                    else:
                        unit_map = {'h': 'hour', 'd': 'day', 'wk': 'week', 'mo': 'month'}
                        u_str = unit_map.get(unit, unit)
                        if period > 1: u_str += "s" # Plural
                        
                        parts.append(f"{freq} times per {int(period)} {u_str}")

            # Code fallback (e.g. BID/TID)
            elif dosage.timing and dosage.timing.code:
                t_text = AppCodeableConcept(dosage.timing.code).readable_value
                if t_text: parts.append(t_text)

            # --- C. AS NEEDED ---
            if dosage.asNeededBoolean:
                parts.append("As needed")
         
            if parts:
                all_lines.append(", ".join(parts))

        if not all_lines:
            return None
          
        return "; ".join(all_lines)


    def to_prompt_string(self, medication_map: Dict[str, 'AppMedication']) -> str:
        # 1. Medication Name Resolution
        med_name_str = "Unknown Medication"
        
        ref_id = self.medication_reference_id
        if ref_id and ref_id in medication_map:
            # Case A: Reference to external Medication resource
            med_name_str = medication_map[ref_id].to_prompt_string()
        elif self.medication_concept_text:
            # Case B: Inline concept
            name = self.medication_concept_text
            
            # Construct code string
            codes_str = ""
            if self.medication_concept_details:
                code_parts = [f"[{d['system']}: {d['code']}]" for d in self.medication_concept_details]
                codes_str = " " + " ".join(code_parts)
            
            med_name_str = f"{name}{codes_str}"

        # 2. Date Management (AuthoredOn)
        date_str = ""
        if self.authored_on:
            date_str = f" (Start: {self.authored_on.strftime('%Y-%m-%d')})"

        # 3. Dosage Management (Using existing dosage_text logic)
        dosage_info = ""
        d_text = self.dosage_text
        if d_text:
            # Indent dosage for visual clarity
            dosage_info = f"\n  Sig: {d_text}"

        # 4. Status On-Hold (If active we don't write it, it's the section default)
        status_warning = ""
        if self.status == MedicationRequestStatus.ON_HOLD:
            status_warning = " [STATUS: ON-HOLD/SUSPENDED]"

        # Output Example: 
        # "- Simvastatin 10 MG [RxNorm: 314231] (Start: 2008-03-03)
        #    Sig: 1, Once a day"
        return f"- {med_name_str}{date_str}{status_warning}{dosage_info}"