'''
Script: device.py
Digital Health Systems and Applications - Project work 2025-2026
Description:
Wrapper class for the HL7 FHIR Device resource. It handles extraction of device status,
types, and names, providing a formatted string representation for LLM grounding.

Group: Carmine Vardaro, Marco Savastano, Francesco Ferrara.
'''

from fhir.resources.device import Device as FhirDevice

from enum import Enum
from typing import Optional, List, Dict

from resources.core.types import AppCodeableConcept

class DeviceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"

    @property
    def definition(self) -> str:
        #https://hl7.org/fhir/R4/valueset-device-status.html
        definitions = {
            "active": "The device is available for use. Note: For *implanted devices* this means that the device is implanted in the patient.",
            "inactive": "The device is no longer available for use (e.g. lost, expired, damaged). Note: For *implanted devices* this means that the device has been removed from the patient.",
            "entered-in-error": "The device was entered in error and voided.",
            "unknown": "The status of the device has not been determined."
        }
        return definitions.get(self.value, "Definition not available.")

class AppDevice:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirDevice(**raw_json_data)

    @property
    def id(self):
        return self.resource.id

    @property
    def status(self) -> Optional[DeviceStatus]:
        if not self.resource.status:
            return None
        try:
            return DeviceStatus(self.resource.status)
        except ValueError:
            return None

    @property
    def device_names(self) -> Optional[str]:
        if not self.resource.deviceName:
            return None
        names = [d.name for d in self.resource.deviceName if d.name]
        if not names:
            return None
        return ", ".join(names)

    @property
    def type_text(self) -> Optional[str]:
        if not self.resource.type:
            return None
        return AppCodeableConcept(self.resource.type).readable_value

    @property
    def type_details(self) -> List[Dict[str, Optional[str]]]:
        if not self.resource.type:
            return []    
        return AppCodeableConcept(self.resource.type).coding_details

    def to_prompt_string(self) -> str:
        # Retrieve the best available name
        standard_name = self.type_text      
        friendly_name = self.device_names 

        # Name display logic
        if standard_name and friendly_name and standard_name.lower() != friendly_name.lower():
            display_name = f"{standard_name} ({friendly_name})"
        else:
            display_name = standard_name or friendly_name or "Unknown Device"

        # Code management (Clean syntax)
        code_str = ""
        if self.type_details:
            code_parts = []
            for c in self.type_details:
                # Direct syntax formatting
                code_parts.append(f"[{c['system']}: {c['code']}]")
            
            if code_parts:
                code_str = " " + " ".join(code_parts)
        
        return f"- {display_name}{code_str}"