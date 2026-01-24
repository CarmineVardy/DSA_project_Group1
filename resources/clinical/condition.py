from fhir.resources.condition import Condition as FhirCondition

class AppCondition:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirCondition(**raw_json_data)

    @property
    def id(self):
        return self.resource.id

    
    
    '''
    clinicalStatus
    verificationStatus
    verificationStatus (?)
    severity
    code
    bodySite (?)
    onset[x] (Quando è iniziata)
    abatement[x] (Quando è finita) (?, lo sappiamo da clinicalStatus se è resolved) 
    recordedDate 
    stage (?)
    note
    '''

