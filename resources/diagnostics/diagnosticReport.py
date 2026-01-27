import base64
from typing import List, Optional
from datetime import datetime

from fhir.resources.diagnosticreport import DiagnosticReport as FhirDiagnosticReport

from resources.core.types import AppCodeableConcept
from resource.diagnostic.enum import *

class AppDiagnosticReport:
    
    def __init__(self, raw_json_data: dict):
        self.resource = FhirDiagnosticReport(**raw_json_data)

    @property
    def id(self) -> str:
        return self.resource.id

    @property
    def status(self) -> DiagnosticReportStatus:
        if not self.resource.status:
            return None
        try:
            return DiagnosticReportStatus(self.resource.status)
        except ValueError:
            return None

    @property
    def category(self) -> Optional[str]:
        if not self.resource.category:
            return None
        
        descriptions = AppCodeableConcept(self.resource.category[0]).all_readable_values
        if not descriptions:
            return None

        return " / ".join(descriptions)

    @property
    def code(self) -> Optional[str]:
        if not self.resource.code:
            return None
            
        descriptions = AppCodeableConcept(self.resource.code).all_readable_values
        if not descriptions:
            return None
            
        return " / ".join(descriptions)

    @property
    def effective_date(self) -> Optional[datetime]:
        return self.resource.effectiveDateTime	

    















'''
presentedForm
   - Reports con allegati: 22397
   - Trovati Base64 (Data): 22348 (Questi vanno decodificati!)
   - Trovati URL (Link):    49
   - Formati (MIME Types):
     * text/plain: 22348
     * text/csv: 49
result
   - Reports collegati a numeri/esami (Observations): 2656 (10.6%)
'''
