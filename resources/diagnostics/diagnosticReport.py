'''
Script: diagnosticReport.py
Digital Health Systems and Applications - Project work 2025-2026
Description:
Wrapper class for the HL7 FHIR DiagnosticReport resource. It handles the extraction
of report status, categories, codes, and most importantly, the decoding of
embedded Base64 clinical notes (presentedForm) for LLM context injection.

Group: Carmine Vardaro, Marco Savastano, Francesco Ferrara.
'''

from fhir.resources.diagnosticreport import DiagnosticReport as FhirDiagnosticReport

import base64
from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime

from resources.core.types import AppCodeableConcept

class DiagnosticReportStatus(str, Enum):
    REGISTERED = "registered"
    PARTIAL = "partial"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    APPENDED = "appended"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"

    @property
    def definition(self) -> str:
        # https://hl7.org/fhir/R4/valueset-event-status.html
        definitions = {
            "registered": "The existence of the report is registered, but there is nothing yet available.",
            "partial": "This is a partial (e.g. initial, interim or preliminary) report: data in the report may be incomplete or unverified.",
            "preliminary": "Verified early results are available, but not all results are final.",
            "final": "The report is complete and verified by an authorized person.",
            "amended": "Subsequent to being final, the report has been modified. This includes any change in the results, diagnosis, narrative text, or other content of a report that has been issued.",
            "corrected": "Subsequent to being final, the report has been modified to correct an error in the report or referenced results.",
            "appended": "Subsequent to being final, the report has been modified by adding new content. The existing content is unchanged.",
            "cancelled": 'The report is unavailable because the measurement was not started or not completed (also sometimes called "aborted").',
            "entered-in-error": 'The report has been withdrawn following a previous final release. This electronic record should never have existed, though it is possible that real-world decisions were based on it. (If real-world activity has occurred, the status should be "cancelled" rather than "entered-in-error".).',
            "unknown": 'The authoring/source system does not know which of the status values currently applies for this observation. Note: This concept is not to be used for "other" - one of the listed statuses is presumed to apply, but the authoring/source system does not know which.'
        }
        return definitions.get(self.value, "Definition not available.")
    
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
    def category_text(self) -> Optional[str]:
        if not self.resource.category: 
            return None
        for cat in self.resource.category:
            val = AppCodeableConcept(cat).readable_value
            if val: return val
        return None

    @property
    def code_text(self) -> Optional[str]:
        if not self.resource.code: return None
        return AppCodeableConcept(self.resource.code).readable_value

    @property
    def code_details(self) -> List[Dict[str, Optional[str]]]:
        if not self.resource.code: return []    
        return AppCodeableConcept(self.resource.code).coding_details

    @property
    def effective_date(self) -> Optional[datetime]:
        return self.resource.effectiveDateTime  

    @property
    def report_text(self) -> Optional[str]:
        """
        Extracts the textual content of the report. 
        It prioritizes the 'conclusion' field, then falls back to decoding 
        base64 'presentedForm' attachments (text/plain).
        """
        if self.resource.conclusion:
            return self.resource.conclusion

        if self.resource.presentedForm:
            for attachment in self.resource.presentedForm:
                
                # We only process plain text attachments
                if not attachment.contentType or not attachment.contentType.startswith("text/plain"):
                    continue
                
                if not attachment.data:
                    continue

                try:
                    b64_string = attachment.data
                    decoded_bytes = base64.b64decode(b64_string)
                    raw_text = decoded_bytes.decode('utf-8')
                    
                    # Basic cleaning of empty lines
                    clean_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                    return "\n".join(clean_lines)
                except Exception:
                    continue
        
        return None

    def to_prompt_string(self) -> str:
        # If no decoded text is available, skip
        text_content = self.report_text
        if not text_content:
            return ""

        title = self.code_text or "Clinical Note"

        # TEXT CLEANING (Crucial for token optimization)
        # Synthea raw text often contains Markdown headers (# Chief Complaint)
        # and repetitions. We compact it while keeping key sections.
        
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        
        # Remove consecutive duplicate lines (common in generated reports)
        cleaned_lines = []
        last_line = ""
        for line in lines:
            if line != last_line:
                cleaned_lines.append(line)
                last_line = line
        
        # Rejoin with indentation for readability in the prompt
        content = "\n  ".join(cleaned_lines) 

        return f"**{title}**:\n  {content}\n"