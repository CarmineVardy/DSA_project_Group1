'''
Script: patient.py
Digital Health Systems and Applications - Project work 2025-2026
Description:
Main wrapper class for the HL7 FHIR Patient resource. It aggregates all related clinical
resources (Conditions, Observations, Medications, etc.) and provides properties for
data extraction and clinical context creation.

Group: Carmine Vardaro, Marco Savastano, Francesco Ferrara.
'''

from fhir.resources.patient import Patient as FhirPatient

from datetime import date, datetime
from enum import Enum
from typing import Optional, List

from resources.administration.device import *
from resources.clinical.allergyIntolerance import *
from resources.clinical.carePlan import *
from resources.clinical.condition import *
from resources.clinical.procedure import *
from resources.diagnostics.diagnosticReport import *
from resources.diagnostics.documentReference import *
from resources.diagnostics.observation import *
from resources.medications.immunization import *
from resources.medications.medicationRequests import *

class Gender(str, Enum):
    # Enum content for gender
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"
    
class AppPatient:
    def __init__(self, raw_json_data: dict):
        self.resource = FhirPatient(**raw_json_data)
        self._devices: List[AppDevice] = []
        self._allergies: List[AppAllergyIntolerance] = []
        self._care_plans: List[AppCarePlan] = []
        self._conditions: List[AppCondition] = []
        self._procedures: List[AppProcedure] = []
        self._diagnostic_reports: List[AppDiagnosticReport] = []
        self._document_references: List[AppDocumentReference] = []
        self._observations: List[AppObservation] = []
        self._immunizations: List[AppImmunization] = []
        self._medication_requests: List[AppMedicationRequest] = []
        
    @property
    def id(self):
        return self.resource.id

    @property
    def gender(self) -> Gender:
        if not self.resource.gender:
            return None
        try:
            return Gender(self.resource.gender)
        except ValueError:
            return None

    @property
    def birth_date(self) -> Optional[date]:
        return self.resource.birthDate

    @property
    def age(self) -> int:
        if not self.birth_date:
            return -1
        born = self.birth_date
        simulated_today = self.last_interaction_date

        return simulated_today.year - born.year - ((simulated_today.month, simulated_today.day) < (born.month, born.day))

    @property
    def is_deceased(self) -> bool:
        if self.resource.deceasedDateTime:
            return True
        if self.resource.deceasedBoolean is True:
            return True
        return False

    @property
    def deceased_date(self) -> Optional[datetime]:
        if not self.is_deceased:
            return None
        return self.resource.deceasedDateTime

    @property  
    def full_name(self) -> str:
        # If no name
        if not self.resource.name:
            return "Unknown"
        # Take all the names
        formatted_names = [
            f"{' '.join(n.given or [])} {n.family or ''}".strip() or "(Unnamed)"
            for n in self.resource.name
        ]
        # If one name return it
        if len(formatted_names) == 1:
            return formatted_names[0]
        # If more than one name build the string with all
        sfx = {1: 'st', 2: 'nd', 3: 'rd'}
        return "\n".join(f"{i}{sfx.get(i if i < 20 else i % 10, 'th')}: {name}" for i, name in enumerate(formatted_names, 1))

    @property
    def devices(self) -> List[AppDevice]:
        return self._devices

    def add_devices(self, devices: List[AppDevice]):
        self._devices.extend(devices)

    @property
    def allergies(self) -> List[AppAllergyIntolerance]:
        return self._allergies

    def add_allergies(self, allergies: List[AppAllergyIntolerance]):
        self._allergies.extend(allergies)

    @property
    def care_plans(self) -> List[AppCarePlan]:
        return self._care_plans

    def add_care_plans(self, plans: List[AppCarePlan]):
        self._care_plans.extend(plans)

    @property
    def conditions(self) -> List[AppCondition]:
        return self._conditions

    def add_conditions(self, conditions: List[AppCondition]):
        self._conditions.extend(conditions)

    @property
    def procedures(self) -> List[AppProcedure]:
        return self._procedures

    def add_procedures(self, procedures: List[AppProcedure]):
        self._procedures.extend(procedures)

    @property
    def diagnostic_reports(self) -> List[AppDiagnosticReport]:
        return self._diagnostic_reports

    def add_diagnostic_reports(self, reports: List[AppDiagnosticReport]):
        self._diagnostic_reports.extend(reports)

    @property
    def document_references(self) -> List[AppDocumentReference]:
        return self._document_references

    def add_document_references(self, docs: List[AppDocumentReference]):
        self._document_references.extend(docs)

    @property
    def observations(self) -> List[AppObservation]:
        return self._observations

    def add_observations(self, observations: List[AppObservation]):
        self._observations.extend(observations)

    @property
    def immunizations(self) -> List[AppImmunization]:
        return self._immunizations

    def add_immunizations(self, immunizations: List[AppImmunization]):
        self._immunizations.extend(immunizations)

    @property
    def medication_requests(self) -> List[AppMedicationRequest]:
        return self._medication_requests

    def add_medication_requests(self, requests: List[AppMedicationRequest]):
        self._medication_requests.extend(requests)

    @property
    def last_interaction_date(self) -> date:
        """
        Finds the most recent date across all clinical resources (excluding death date).
        This date acts as the simulated "TODAY" for context generation.
        """
        dates = []
        
        # Collect dates from all resources
        dates.extend([r.effective_date for r in self.diagnostic_reports if r.effective_date])
        dates.extend([o.effective_date for o in self.observations if o.effective_date])
        dates.extend([p.end_date or p.start_date for p in self.procedures if p.start_date or p.end_date])
        dates.extend([m.authored_on for m in self.medication_requests if m.authored_on])
        dates.extend([c.onset_date for c in self.conditions if c.onset_date])

        # Convert everything to pure date (without time) and filter None
        valid_dates = []
        for d in dates:
            if isinstance(d, datetime):
                valid_dates.append(d.date())
            elif isinstance(d, date):
                valid_dates.append(d)
        
        if not valid_dates:
            return date.today() # Fallback if patient history is empty
            
        return max(valid_dates)


    def generate_clinical_context(self, medication_map: Dict[str, 'AppMedication']) -> str:
        """
        Generates a comprehensive clinical summary of the patient for LLM grounding.
        Args:
            medication_map: A dictionary mapping reference IDs to Medication resources (used to resolve medication details in requests).
        Returns:
            A formatted string containing the patient's clinical context.
        """
        
        simulated_today = self.last_interaction_date
        simulated_today_str = simulated_today.strftime('%Y-%m-%d')

        context_parts = []
        
        context_parts.append(f"(Current Date: {simulated_today_str})")
                
        # --- DEMOGRAPHICS ---
        context_parts.append("### PATIENT PROFILE")
        gender_str = self.gender.value if self.gender else "Unknown"
        age_str = f"{self.age} years old" if self.age >= 0 else "Age unknown"
        context_parts.append(f"- Demographics: {gender_str}, {age_str}")

        # --- DEVICES ---
        active_devices = [d for d in self.devices if d.status == DeviceStatus.ACTIVE]
        if active_devices:
            context_parts.append("\n### ACTIVE DEVICES")
            for device in active_devices:
                context_parts.append(device.to_prompt_string())
        else:
            context_parts.append("\n### ACTIVE DEVICES\n- None")

        # --- ALLERGIES & INTOLERANCES ---
        active_allergies = []
        for a in self.allergies:
            is_active = a.clinical_status not in [AllergyClinicalStatus.INACTIVE, AllergyClinicalStatus.RESOLVED]
            is_valid = a.verification_status not in [AllergyVerificationStatus.REFUTED, AllergyVerificationStatus.ENTERED_IN_ERROR]
            if is_active and is_valid:
                active_allergies.append(a)
        
        if active_allergies:
            context_parts.append("\n### ALLERGIES & INTOLERANCES")
            
            # Bucketing categories
            food_allergies = []
            med_allergies = []
            env_allergies = []
            other_allergies = [] # Biologic or null
            
            for a in active_allergies:
                cat = a.category
                if cat == AllergyCategory.FOOD:
                    food_allergies.append(a)
                elif cat == AllergyCategory.MEDICATION:
                    med_allergies.append(a)
                elif cat == AllergyCategory.ENVIRONMENT:
                    env_allergies.append(a)
                else:
                    other_allergies.append(a)
            
            # Helper function to print subsections
            def add_subsection(title, items):
                if items:
                    context_parts.append(f"**{title}**") # Markdown bold subtitle
                    for item in items:
                        context_parts.append(item.to_prompt_string())

            # Add sections in priority order
            add_subsection("Medication/Drugs", med_allergies)
            add_subsection("Food/Dietary", food_allergies)
            add_subsection("Environment", env_allergies)
            add_subsection("Other/Biologic", other_allergies)

        else:
            context_parts.append("\n### ALLERGIES & INTOLERANCES\n- No known allergies")

        # --- CARE PLANS ---
        active_plans = [
            cp for cp in self.care_plans 
            if cp.status == CarePlanStatus.ACTIVE
        ]

        if active_plans:
            context_parts.append("\n### ACTIVE CARE PLANS & GOALS")
            for plan in active_plans:
                plan_str = plan.to_prompt_string()
                if plan_str: # Avoid empty plans without activities
                    context_parts.append(plan_str)

        # --- CONDITIONS (Problem List) ---
        relevant_statuses = [
            ConditionClinicalStatus.ACTIVE,
            ConditionClinicalStatus.RECURRENCE,
            ConditionClinicalStatus.RELAPSE,
            None 
        ]
        
        active_conditions = [
            c for c in self.conditions
            if c.clinical_status in relevant_statuses
            and c.verification_status not in [ConditionVerificationStatus.REFUTED, ConditionVerificationStatus.ENTERED_IN_ERROR]
        ]

        if active_conditions:
            active_conditions.sort(key=lambda x: x.onset_date or datetime.min)
            context_parts.append("\n### ACTIVE CONDITIONS (PROBLEM LIST)")
            
            # Deduplication based on final string
            seen_conditions = set()
            for cond in active_conditions:
                s = cond.to_prompt_string()
                if s and s not in seen_conditions:
                    context_parts.append(s)
                    seen_conditions.add(s)
        else:
             context_parts.append("\n### ACTIVE CONDITIONS (PROBLEM LIST)\n- No active conditions reported")

        # --- PROCEDURES HISTORY ---
        valid_statuses = [ProcedureStatus.COMPLETED, ProcedureStatus.IN_PROGRESS, None]
        
        valid_procedures = [
            p for p in self.procedures 
            if p.status in valid_statuses
        ]

        if valid_procedures:
            context_parts.append("\n### PROCEDURES HISTORY")
            
            # Grouping: Key = (Name, CodeString) -> Value = [Dates]
            from collections import defaultdict
            proc_groups = defaultdict(list)
            
            # List for undated procedures (rare but possible)
            undated_procs = []

            for p in valid_procedures:
                name = p.code_text or "Unknown Procedure"
                codes = p.simple_code_str
                
                if p.start_date:
                    proc_groups[(name, codes)].append(p.start_date)
                else:
                    # If undated, use standard method and save separately
                    undated_procs.append(p.to_prompt_string())

            # Formatting grouped dates
            for (name, codes), dates in proc_groups.items():
                dates.sort()
                
                if len(dates) == 1:
                    # Single case: Show simple date
                    date_display = f" [Date: {dates[0].strftime('%Y-%m-%d')}]"
                elif len(dates) <= 5:
                    # Few events: List all
                    date_strs = [d.strftime('%Y-%m-%d') for d in dates]
                    date_display = f" (Dates: {', '.join(date_strs)})"
                else:
                    # Many events: Show Count and Range (First...Last)
                    # Useful for chronic therapies (e.g. Dialysis, Chemotherapy)
                    first = dates[0].strftime('%Y-%m-%d')
                    last = dates[-1].strftime('%Y-%m-%d')
                    date_display = f" (Count: {len(dates)} occurrences, Range: {first} to {last})"
                
                context_parts.append(f"- {name}{date_display}{codes}")

            # Add undated procedures (if any)
            # Use set to deduplicate exact strings
            if undated_procs:
                for s in sorted(list(set(undated_procs))):
                    context_parts.append(s)
        
        # --- IMMUNIZATIONS ---
        valid_immunizations = [
            i for i in self.immunizations 
            if i.status == ImmunizationStatus.COMPLETED
        ]

        if valid_immunizations:
            context_parts.append("\n### IMMUNIZATION HISTORY")
            
            # Grouping Dictionary: Key = (Name, CodeString) -> Value = [Dates]
            from collections import defaultdict
            vaccine_groups = defaultdict(list)
            
            for imm in valid_immunizations:
                name = imm.code_text or "Unknown Vaccine"
                code_str = imm.simple_code_str 
                
                # Use tuple as unique key for vaccine
                key = (name, code_str)
                
                if imm.occurrence_date:
                    vaccine_groups[key].append(imm.occurrence_date)
            
            # Iterate groups and format output intelligently
            for (name, codes), dates in vaccine_groups.items():
                # Sort dates oldest to newest
                dates.sort()
                
                # Date formatting
                if not dates:
                    date_display = ""
                elif len(dates) > 5:
                    # "INFLUENZA SPAM" CASE: Too many dates. Show count and latest.
                    last_date = dates[-1].strftime('%Y-%m-%d')
                    date_display = f" ({len(dates)} doses, Latest: {last_date})"
                else:
                    # NORMAL CASE: Show all dates
                    date_strings = [d.strftime('%Y-%m-%d') for d in dates]
                    date_display = f" (Dates: {', '.join(date_strings)})"
                
                # Final grouped output
                context_parts.append(f"- {name}{date_display}{codes}")

        # --- MEDICATION REQUESTS ---
        valid_statuses = [MedicationRequestStatus.ACTIVE, MedicationRequestStatus.ON_HOLD]
        
        current_meds = [
            m for m in self.medication_requests 
            if m.status in valid_statuses
        ]

        if current_meds:
            context_parts.append("\n### CURRENT MEDICATIONS (ACTIVE)")
            
            # Sort by prescription date (newest first)
            current_meds.sort(key=lambda x: x.authored_on or datetime.min, reverse=True)
            
            # Deduplication based on generated string
            seen_meds = set()
            for med in current_meds:
                # Pass map to resource method
                s = med.to_prompt_string(medication_map)
                
                if s and s not in seen_meds:
                    context_parts.append(s)
                    seen_meds.add(s)
        else:
             context_parts.append("\n### CURRENT MEDICATIONS (ACTIVE)\n- No active medications")

        # --- OBSERVATIONS ---
        valid_obs = [
            o for o in self.observations 
            if o.status in [ObservationStatus.FINAL, ObservationStatus.AMENDED, ObservationStatus.CORRECTED]
        ]

        if valid_obs:
            # Group by (Name) -> List
            obs_groups = {}
            for o in valid_obs:
                key = o.code_text or "Unknown"
                if key not in obs_groups:
                    obs_groups[key] = []
                obs_groups[key].append(o)

            # Snapshot (Take only the most recent for each type)
            latest_observations = []
            for key, obs_list in obs_groups.items():
                # Sort by date (oldest to newest)
                obs_list.sort(key=lambda x: x.effective_date or datetime.min)
                latest_observations.append(obs_list[-1])

            # Categorization (Bucketing)
            vitals_list = []
            labs_list = []
            social_list = []
            other_list = [] # Survey, Imaging, Exam, Procedure, etc.

            for o in latest_observations:
                cat = o.category
                
                if cat == ObservationCategory.VITAL_SIGNS:
                    vitals_list.append(o)
                elif cat == ObservationCategory.LABORATORY:
                    labs_list.append(o)
                elif cat == ObservationCategory.SOCIAL_HISTORY:
                    social_list.append(o)
                else:
                    # Group Imaging, Exam, Survey, Procedure into one block "Findings"
                    other_list.append(o)
            
            # Helper Print Function
            def print_obs_section(title, items):
                if items:
                    context_parts.append(f"\n### {title}")
                    # Alphabetical order for cleanliness
                    items.sort(key=lambda x: x.code_text or "")
                    for item in items:
                        context_parts.append(item.to_prompt_string())

            # Generate Sections in Prompt
            print_obs_section("LATEST VITAL SIGNS", vitals_list)
            print_obs_section("SOCIAL HISTORY & LIFESTYLE", social_list)
            print_obs_section("LATEST LABORATORY RESULTS", labs_list)
            print_obs_section("OTHER CLINICAL FINDINGS (Surveys, Imaging, Exams)", other_list)

        # --- DIAGNOSTIC REPORT (Latest Clinical Note) ---
        text_reports = []
        for r in self.diagnostic_reports:
            # Check if report has text content
            if r.report_text:
                text_reports.append(r)
                
        if text_reports:
            text_reports.sort(key=lambda x: x.effective_date or datetime.min)            
            latest_report = text_reports[-1]
            context_parts.append("\n### LATEST CLINICAL NOTE")
            context_parts.append(latest_report.to_prompt_string())

        return "\n".join(context_parts)