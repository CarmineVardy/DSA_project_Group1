from enum import Enum

# ==========================================
# OBSERVATION ENUMS
# ==========================================

class ObservationStatus(str, Enum):
    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"

class ObservationCategory(str, Enum):
    # Standard FHIR categories (http://terminology.hl7.org/CodeSystem/observation-category)
    SOCIAL_HISTORY = "social-history"
    VITAL_SIGNS = "vital-signs"
    IMAGING = "imaging"
    LABORATORY = "laboratory"
    PROCEDURE = "procedure"
    SURVEY = "survey"
    EXAM = "exam"
    THERAPY = "therapy"
    ACTIVITY = "activity"
    UNKNOWN = "unknown"

    @property
    def display_name(self) -> str:
        """Returns a readable name for the prompt."""
        return self.value.replace("-", " ").title()


# ==========================================
# DIAGNOSTIC REPORT ENUMS
# ==========================================

class DiagnosticReportStatus(str, Enum):
    # Standard FHIR values
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