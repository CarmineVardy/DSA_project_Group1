from typing import List, Optional, Union
from datetime import datetime
from fhir.resources.observation import Observation as FhirObservation
from fhir.resources.codeableconcept import CodeableConcept

# Import Core Types
from resources.core.types import AppCodeableConcept

# Import Local Enums
from .enums import ObservationStatus, ObservationCategory

class AppObservation:
    """
    Wrapper for FHIR Observation resource.
    Handles polymorphism of value[x] and component structures specifically for LLM Prompts.
    """
    def __init__(self, raw_json_data: dict):
        self.resource = FhirObservation(**raw_json_data)

    @property
    def id(self) -> str:
        return self.resource.id

    # ==========================================================================
    # 1. METADATA & CLASSIFICATION
    # ==========================================================================

    @property
    def status(self) -> ObservationStatus:
        """
        Status is a simple code string in FHIR (not a CodeableConcept).
        We map it directly to our Enum.
        """
        if not self.resource.status:
            return ObservationStatus.UNKNOWN
        try:
            return ObservationStatus(self.resource.status)
        except ValueError:
            return ObservationStatus.UNKNOWN

    @property
    def category_names(self) -> List[str]:
        """
        Returns readable category names (e.g. ['Vital Signs', 'Laboratory']).
        Useful for grouping data in the Prompt.
        """
        if not self.resource.category:
            return []
        
        return [
            AppCodeableConcept(cat).readable_value 
            for cat in self.resource.category 
            if AppCodeableConcept(cat).readable_value
        ]

    @property
    def category_enum(self) -> List[ObservationCategory]:
        """
        Returns Enums for logic filtering (e.g. 'if category == LABORATORY').
        """
        if not self.resource.category:
            return []
        
        return [
            AppCodeableConcept(cat).bind_to(ObservationCategory) 
            for cat in self.resource.category
        ]

    @property
    def name(self) -> Optional[str]:
        """
        The name of the test (e.g., 'Hemoglobin', 'Body Weight').
        """
        if not self.resource.code:
            return None
        return AppCodeableConcept(self.resource.code).readable_value

    @property
    def effective_date(self) -> Optional[datetime]:
        """
        The clinically relevant date/time of the observation.
        """
        return self.resource.effectiveDateTime

    # ==========================================================================
    # 2. RESULT VALUE (The Core Logic)
    # ==========================================================================

    @property
    def value(self) -> Optional[str]:
        """
        Smart property that returns the best string representation of the result.
        It handles:
        1. Quantity (12 kg)
        2. CodeableConcept (Yellow)
        3. String (Negative)
        4. Components (Systolic: 120 mmHg, Diastolic: 80 mmHg)
        """
        r = self.resource

        # CASE A: Value Quantity (Most common: 90%)
        if r.valueQuantity:
            val = r.valueQuantity.value
            unit = r.valueQuantity.unit or ""
            return f"{val} {unit}".strip()

        # CASE B: Value CodeableConcept (Qualitative: 4%)
        if r.valueCodeableConcept:
            return AppCodeableConcept(r.valueCodeableConcept).readable_value

        # CASE C: Value String (Rare: 0.1%)
        if r.valueString:
            return r.valueString

        # CASE D: Components (e.g., Blood Pressure: 5%)
        # If the main value is missing, we check components.
        if r.component:
            parts = []
            for c in r.component:
                # 1. Get readable name of the component (e.g., "Systolic blood pressure")
                c_name = AppCodeableConcept(c.code).readable_value or "Unknown Component"
                
                # 2. Get value (Usually Quantity)
                c_value = "N/A"
                if c.valueQuantity:
                    val = c.valueQuantity.value
                    unit = c.valueQuantity.unit or ""
                    c_value = f"{val} {unit}".strip()
                elif c.valueString:
                    c_value = c.valueString
                elif c.valueCodeableConcept:
                    c_value = AppCodeableConcept(c.valueCodeableConcept).readable_value
                
                parts.append(f"{c_name}: {c_value}")
            
            # Join them: "Systolic: 120 mmHg, Diastolic: 80 mmHg"
            return ", ".join(parts)

        # CASE E: Nothing found
        return None


'''
Quindi dobbiamo modellare:
status
category,
code
effectiveDateTime
value per:
valueQuantity       
valueCodeableConcept   
valueString   
valueSampledData (raro..per ora manca)
poi il caso con
component dove dobbiamo prendere:
code  e valueQuantity.
'''