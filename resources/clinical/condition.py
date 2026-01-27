from fhir.resources.condition import Condition as FhirCondition

from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Dict

from resources.core.types import AppCodeableConcept
from resources.clinical.enum import *

class AppCondition:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirCondition(**raw_json_data)

    @property
    def id(self):
        return self.resource.id

    @property
    def clinical_status(self) -> Optional[ClinicalStatus]:
        if not self.resource.clinicalStatus:
            return None    
        return AppCodeableConcept(self.resource.clinicalStatus).bind_to(ClinicalStatus)
    
    @property
    def verification_status(self) -> Optional[VerificationStatus]:
        if not self.resource.verificationStatus:
            return None 
        return AppCodeableConcept(self.resource.verificationStatus).bind_to(VerificationStatus)

    @property
    def categories(self) -> List[ConditionCategory]:
        if not self.resource.category:
            return []

        return [
            AppCodeableConcept(cat).bind_to(ConditionCategory) 
            for cat in self.resource.category
        ]

    @property
    def code(self) -> Optional[str]:
        if not self.resource.code:
            return None 
        return AppCodeableConcept(self.resource.code).readable_value

    @property
    def code_details(self) -> List[Dict[str, str]]:
        if not self.resource.code:
            return []    
        return AppCodeableConcept(self.resource.code).all_codings_details

    @property
    def onset_date(self) -> Optional[datetime]:
        return self.resource.onsetDateTime

    @property
    def abatement_date(self) -> Optional[datetime]:
        return self.resource.abatementDateTime