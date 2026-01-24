from fhir.resources.patient import Patient as FhirPatient

from datetime import date, datetime
from enum import Enum
from typing import Optional, List

from resources.clinical.condition import AppCondition

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"
    
    def __str__(self):
        return self.value

class AppPatient:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirPatient(**raw_json_data)
        self._conditions: List[AppCondition] = []

    @property
    def id(self):
        return self.resource.id

    @property
    def gender(self) -> Gender:
        if not self.resource.gender:
            return Gender.UNKNOWN
        return Gender(self.resource.gender)

    @property
    def birthDate(self) -> Optional[date]:
        return self.resource.birthDate

    @property
    def age(self) -> int:
        if not self.birthDate:
            return -1
        born = self.birthDate
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @property
    def isDeceased(self) -> bool:
        if self.resource.deceasedDateTime:
            return True
        if self.resource.deceasedBoolean is True:
            return True
        return False

    @property
    def deceasedDate(self) -> Optional[datetime]:
        if not self.isDeceased:
            return None
        return self.resource.deceasedDateTime
        
    def get_full_name(self) -> str:
        #If no name
        if not self.resource.name:
            return "Unknown"

        #Take all the names
        formatted_names = [
            f"{' '.join(n.given or [])} {n.family or ''}".strip() or "(Unnamed)"
            for n in self.resource.name
        ]

        #If one name return it
        if len(formatted_names) == 1:
            return formatted_names[0]

        #If more than one name build the string with all
        suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
        return "; ".join(f"{i}{sfx.get(i, 'th')}: {name}" for i, name in enumerate(formatted_names, 1))

    @property
    def conditions(self) -> List[AppCondition]:
        return self._conditions

    def add_conditions(self, conditions: List[AppCondition]):
        self._conditions.extend(conditions)











    #UTIL METHODS THAT CAN BE USEFUL
    def __eq__(self, other):
        if not isinstance(other, AppPatient):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return ""
            


