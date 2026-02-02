'''
Script: carePlan.py
Digital Health Systems and Applications - Project work 2025-2026
Description:
Wrapper class for the HL7 FHIR CarePlan resource. It manages care plan details,
including status, intent, active periods, and the summary of planned activities
to be included in the patient's clinical context.

Group: Carmine Vardaro, Marco Savastano, Francesco Ferrara.
'''

from fhir.resources.careplan import CarePlan as FhirCarePlan

from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime

from resources.core.types import AppCodeableConcept

class CarePlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    REVOKED = "revoked"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"

    @property
    def definition(self) -> str:
        #https://hl7.org/fhir/R4/valueset-request-status.html
        definitions = {
            "draft": "The request has been created but is not yet complete or ready for action.",
            "active": "The request is in force and ready to be acted upon.",
            "on-hold": "The request (and any implicit authorization to act) has been temporarily withdrawn but is expected to resume in the future.",
            "revoked": "The request (and any implicit authorization to act) has been terminated prior to the known full completion of the intended actions. No further activity should occur.",
            "completed": "The activity described by the request has been fully performed. No further activity will occur.",
            "entered-in-error": 'This request should never have existed and should be considered "void". (It is possible that real-world decisions were based on it. If real-world activity has occurred, the status should be "revoked" rather than "entered-in-error".).',
            "unknown": 'The authoring/source system does not know which of the status values currently applies for this request. Note: This concept is not to be used for "other" - one of the listed statuses is presumed to apply, but the authoring/source system does not know which.'
        }
        return definitions.get(self.value, "Definition not available.")

class CarePlanIntent(str, Enum):
    PROPOSAL = "proposal"
    PLAN = "plan"
    ORDER = "order"
    OPTION = "option"

    @property
    def definition(self) -> str:
        #https://hl7.org/fhir/R4/valueset-care-plan-intent.html
        definitions = {
            "proposal": "The request is a suggestion made by someone/something that does not have an intention to ensure it occurs and without providing an authorization to act.",
            "plan": "The request represents an intention to ensure something occurs without providing an authorization for others to act.",
            "order": "The request represents a request/demand and authorization for action by a Practitioner.",
            "option": "The request represents a component or option for a RequestGroup that establishes timing, conditionality and/or other constraints among a set of requests. Refer to [[[RequestGroup]]] for additional information on how this status is used."
        }
        return definitions.get(self.value, "Definition not available.")

class CarePlanActivityStatus(str, Enum):
    NOT_STARTED = "not-started"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in-progress"
    ON_HOLD = "on-hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    STOPPED = "stopped"
    UNKNOWN = "unknown"
    ENTERED_IN_ERROR = "entered-in-error"

    @property
    def definition(self) -> str:
        #https://hl7.org/fhir/R4/valueset-care-plan-activity-status.html
        definitions = {
            "not-started": "Care plan activity is planned but no action has yet been taken.",
            "scheduled": "Appointment or other booking has occurred but activity has not yet begun.",
            "in-progress": "Care plan activity has been started but is not yet complete.",
            "on-hold": "Care plan activity was started but has temporarily ceased with an expectation of resumption at a future time.",
            "completed": "Care plan activity has been completed (more or less) as planned.",
            "cancelled": "The planned care plan activity has been withdrawn.",
            "stopped": "The planned care plan activity has been ended prior to completion after the activity was started.",
            "unknown": 'The current state of the care plan activity is not known. Note: This concept is not to be used for "other" - one of the listed statuses is presumed to apply, but the authoring/source system does not know which one.',
            "entered-in-error": "Care plan activity was entered in error and voided."
        }
        return definitions.get(self.value, "Definition not available.")


class AppCarePlan:

    def __init__(self, raw_json_data: dict):
        self.resource = FhirCarePlan(**raw_json_data)

    @property
    def id(self):
        return self.resource.id

    @property
    def status(self) -> Optional[CarePlanStatus]:
        if not self.resource.status: 
            return None
        try: 
            return CarePlanStatus(self.resource.status)
        except ValueError: 
            return None

    @property
    def intent(self) -> Optional[CarePlanIntent]:
        if not self.resource.intent: 
            return None
        try: 
            return CarePlanIntent(self.resource.intent)
        except ValueError: 
            return None

    @property
    def category_text(self) -> Optional[str]:
        if not self.resource.category: 
            return None
        for cat in self.resource.category:
            val = AppCodeableConcept(cat).readable_value
            if val: return val
        return None

    @property
    def start_date(self) -> Optional[datetime]:
        if self.resource.period and self.resource.period.start:
            return self.resource.period.start
        return None

    @property
    def end_date(self) -> Optional[datetime]:
        if self.resource.period and self.resource.period.end:
            return self.resource.period.end
        return None

    @property
    def activities_summary(self) -> List[Dict]:
        if not self.resource.activity:
            return []
        
        results = []
        for act in self.resource.activity:
            if not act.detail:
                continue
            detail = act.detail
            
            act_text = None
            if detail.code:
                act_text = AppCodeableConcept(detail.code).readable_value
               
            if not act_text:
                continue 

            raw_status = detail.status
            safe_status = None
            if raw_status:
                try:
                    safe_status = CarePlanActivityStatus(raw_status)
                except ValueError:
                    safe_status = None

            act_codes = []
            if detail.code:
                act_codes = AppCodeableConcept(detail.code).coding_details

            results.append({
                'text': act_text,
                'status': safe_status, # Can be None
                'codes': act_codes
            })
            
        return results

    def to_prompt_string(self) -> str:
        if not self.activities_summary:
            return ""

        # Plan Header: **Plan Name** (Start: YYYY-MM-DD)
        header_name = self.category_text or "General Care Plan"
        date_info = f" (Start: {self.start_date.strftime('%Y-%m-%d')})" if self.start_date else ""
        header_line = f"**{header_name}**{date_info}"

        # Build Activities (with Deduplication)
        activity_lines = []
        seen_activities = set() # Avoid duplicates

        for act in self.activities_summary:
            text = act['text']
            
            # Skip duplicates or empty text
            if not text or text in seen_activities:
                continue
            seen_activities.add(text)

            # Activity Status Management
            status_str = ""
            if act['status']:
                status_str = f" ({act['status'].value})"

            # Code Management (Clean syntax)
            code_str = ""
            if act['codes']:
                code_parts = []
                for c in act['codes']:
                    code_parts.append(f"[{c['system']}: {c['code']}]")
                if code_parts:
                    code_str = " " + " ".join(code_parts)

            # Final Line: - Activity Name (Status) [System: Code]
            activity_lines.append(f"- {text}{status_str}{code_str}")

        if not activity_lines:
            return ""

        return f"{header_line}\n" + "\n".join(activity_lines)