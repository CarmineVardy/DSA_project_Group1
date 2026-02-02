'''
Script: documentReference.py
Digital Health Systems and Applications - Project work 2025-2026
Description:
Wrapper class for the HL7 FHIR DocumentReference resource. It manages document metadata
(status, type, category) and handles the extraction and decoding of embedded
Base64 text content for use in the clinical summary.

Group: Carmine Vardaro, Marco Savastano, Francesco Ferrara.
'''

from fhir.resources.documentreference import DocumentReference as FhirDocumentReference

import base64
from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime

from resources.core.types import AppCodeableConcept

class DocumentReferenceStatus(str, Enum):
   CURRENT = "current"
   SUPERSEDED = "superseded"
   ENTERED_IN_ERROR = "entered-in-error"

   @property
   def definition(self) -> str:
      # https://hl7.org/fhir/R4/valueset-document-reference-status.html
      definitions = {
         "current": "This is the current reference for this document.",
         "superseded": "This reference has been superseded by another reference.",
         "entered-in-error": "This reference was created in error."
      }
      return definitions.get(self.value, "Definition not available.")

class AppDocumentReference:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirDocumentReference(**raw_json_data)

    @property
    def id(self):
        return self.resource.id

    @property
    def status(self) -> Optional[DocumentReferenceStatus]:
        if not self.resource.status:
            return None
        try:
            return DocumentReferenceStatus(self.resource.status)
        except ValueError:
            return None

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

    @property
    def category_text(self) -> Optional[str]:
        if not self.resource.category:
            return None
        for cat in self.resource.category:
            val = AppCodeableConcept(cat).readable_value
            if val:
                return val
        return None

    @property
    def category_details(self) -> List[Dict[str, Optional[str]]]:
        if not self.resource.category:
            return []
        all_details = []
        for cat in self.resource.category:
            details = AppCodeableConcept(cat).coding_details
            all_details.extend(details)
        return all_details

    @property
    def date(self) -> Optional[datetime]:
        return self.resource.date
        
    @property
    def content_text(self) -> Optional[str]:
        """
        Decodes Base64 encoded text content from the document attachment.
        Only processes attachments with 'text/' content types.
        """
        if not self.resource.content:
            return None
        for content_entry in self.resource.content:
            attachment = content_entry.attachment
            if not attachment or not attachment.data:
                continue
            if not attachment.contentType.startswith("text/"):
                continue
            try:
                b64_string = attachment.data
                decoded_bytes = base64.b64decode(b64_string)
                raw_text = decoded_bytes.decode('utf-8')
                # Clean up empty lines
                clean_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                return "\n".join(clean_lines)
            except Exception as e:
                continue
        return None

    def to_prompt_string(self) -> str:
        """
        Formats the document for the LLM prompt.
        Format:
        - Title:
          [Indented Content]
        """
        # 1. Retrieve text content
        text_content = self.content_text
        if not text_content:
            return ""

        # 2. Header
        # Use type_text or category_text. Add final colon.
        title = self.type_text or self.category_text or ""
        header_line = f"- {title}:"

        # 3. Content Indentation
        # Add 2 spaces before each line to visually align under the title
        indented_lines = [f"  {line}" for line in text_content.splitlines()]
        formatted_content = "\n".join(indented_lines)

        return f"{header_line}\n{formatted_content}\n"