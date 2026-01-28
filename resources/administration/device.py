from fhir.resources.device import Device as FhirDevice
from fhir.resources.codeableconcept import CodeableConcept
from typing import Optional, List, Dict, Any

class AppDevice:
    
    UC1_SELECTED = [
        "Coronary artery stent",
        "Left ventricular assist device"
    ]

    UC2_SELECTED = [
        "Coronary artery stent",
        "Implantable cardiac pacemaker",
        "Implantable defibrillator",
        "Left ventricular assist device"
    ]

    SNOMED_MAPPING: Dict[str, str] = {
        "Coronary artery stent": "705643001",
        "Left ventricular assist device": "360066001",
        "Implantable cardiac pacemaker": "706004007",
        "Implantable defibrillator": "72506001"
    }

    def __init__(self, raw_json_data: dict):
        self.raw = raw_json_data
        
        # Compatibility Layer R4 -> R5
        adapted_data = self._apply_compatibility_layer(raw_json_data)
        
        try:
            self.resource = FhirDevice(**adapted_data)
        except Exception:
            self.resource = None

    def _apply_compatibility_layer(self, data: dict) -> dict:
        clean_data = data.copy()

        # 1. Handle deviceName
        # R4: [{'name': 'X', 'type': 'Y'}]
        # R5: [{'value': 'X', 'type': 'Y'}]
        if 'deviceName' in clean_data:
            # Rename field to standard R5 'name'
            # Rename internal key 'name' to 'value'
            r4_names = clean_data.pop('deviceName')
            r5_names = []
            for item in r4_names:
                r5_item = item.copy()
                if 'name' in r5_item:
                    r5_item['value'] = r5_item.pop('name')
                r5_names.append(r5_item)
            clean_data['name'] = r5_names

        # 2. Handle type (R4: Object -> R5: List of Objects)
        # In R5 'type' is [CodeableConcept], in R4 it is CodeableConcept.
        # This often causes validation error. We remove it for safety 
        # and access via raw.
        if 'type' in clean_data:
            del clean_data['type']

        # 3. Remove R4-only or top-level fields that moved or were removed
        # 'patient', 'distinctIdentifier', 'owner', 'location' are not in R5 Device root
        keys_to_remove = ['patient', 'distinctIdentifier', 'owner', 'location', 'parent']
        for key in keys_to_remove:
            if key in clean_data:
                del clean_data[key]
                
        return clean_data

    def get_snomed_code(self, device_name: str) -> Optional[str]:
        return self.SNOMED_MAPPING.get(device_name)

    def check_is_selected(self, use_case: str) -> bool:
        current_name = self.deviceName.strip()
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
    def deviceName(self) -> str:
        # Try R5 'name'
        if self.resource and self.resource.name:
            # Return the first name found
            return self.resource.name[0].value
        
        # Try R4 'deviceName'
        raw_names = self.raw.get('deviceName', [])
        if raw_names:
            return raw_names[0].get('name', "Unknown Device")
        
        # Try R4 'type' fallback
        type_concept = self.raw.get('type')
        return self._get_concept_display_raw(type_concept) or "Unknown Device"

    @property
    def distinctIdentifier(self) -> str:
        # R4 field
        return self.raw.get('distinctIdentifier') or "None"

    @property
    def expirationDate(self) -> str:
        if self.resource and self.resource.expirationDate:
            return str(self.resource.expirationDate)
        return self.raw.get('expirationDate') or "None"

    @property
    def lotNumber(self) -> str:
        if self.resource and self.resource.lotNumber:
            return self.resource.lotNumber
        return self.raw.get('lotNumber') or "None"

    @property
    def manufactureDate(self) -> str:
        if self.resource and self.resource.manufactureDate:
            return str(self.resource.manufactureDate)
        return self.raw.get('manufactureDate') or "None"

    @property
    def serialNumber(self) -> str:
        if self.resource and self.resource.serialNumber:
            return self.resource.serialNumber
        return self.raw.get('serialNumber') or "None"

    @property
    def type(self) -> str:
        # Use raw because we removed it from init to avoid List vs Object issues
        raw_type = self.raw.get('type')
        return self._get_concept_display_raw(raw_type) or "Unknown"

    @property
    def udiCarrier(self) -> List[Dict[str, str]]:
        # R5 and R4 have similar structure, but safer to parse raw
        carriers = self.raw.get('udiCarrier', [])
        results = []
        for c in carriers:
            results.append({
                "deviceIdentifier": c.get('deviceIdentifier', 'N/A'),
                "carrierHRF": c.get('carrierHRF', 'N/A')
            })
        return results

    @property
    def patient(self) -> str:
        # R4 field
        pat = self.raw.get('patient', {})
        return pat.get('display') or pat.get('reference') or "None"

    @property
    def meta(self) -> Dict[str, Any]:
        return self.raw.get('meta', {})

    @property
    def resourceType(self) -> str:
        return self.raw.get('resourceType', 'Device')

    def _get_concept_display_raw(self, raw_concept: dict) -> Optional[str]:
        if not raw_concept: return None
        if raw_concept.get('text'): return raw_concept['text']
        codings = raw_concept.get('coding', [])
        for coding in codings:
            if coding.get('display'): return coding['display']
        return None

    def __eq__(self, other):
        if not isinstance(other, AppDevice): return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        lines = [
            f"ID: {self.id}",
            f"Device Name: {self.deviceName}",
            f"Status: {self.status}",
            f"Type: {self.type}",
            f"Distinct ID: {self.distinctIdentifier}",
            f"Lot Number: {self.lotNumber}",
            f"Serial Number: {self.serialNumber}",
            f"Expiration Date: {self.expirationDate}",
            f"Manufacture Date: {self.manufactureDate}",
            f"Patient: {self.patient}"
        ]
        return "\n".join(lines)