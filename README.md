# Digital Health Systems and Applications - Project Work 2025-2026

**Project Title:** LLM-based Clinical Decision Support System (CDSS)
**Academic Year:** 2025/2026  

### Group Members:
* **Carmine Vardaro**
* **Marco Savastano**
* **Francesco Ferrara**

## 📂 Project Structure

The codebase is organized to separate the UI/main logic from the data modeling layer. The `resources` folder contains wrapper classes that handle FHIR resources.

code/
├── main_app.py                 # Main entry point (Streamlit UI & Logic)
└── resources/                  # Abstraction layer for FHIR Resources
    ├── administration/
    │   ├── device.py           # Handles implanted/active devices
    │   └── patient.py          # Main Patient wrapper & Context Generator
    ├── clinical/
    │   ├── allergyIntolerance.py # Allergy status, criticality, categories
    │   ├── carePlan.py         # Active care plans & planned activities
    │   ├── condition.py        # Problem list (Active conditions)
    │   └── procedure.py        # Procedure history & status
    ├── core/
    │   └── types.py            # Helper for CodeableConcept & Enum binding
    ├── diagnostics/
    │   ├── diagnosticReport.py # Labs/Notes (Handles Base64 text decoding)
    │   ├── documentReference.py# External documents (CDA/PDF text extraction)
    │   └── observation.py      # Vital signs & Lab results (LOINC/SNOMED)
    ├── medications/
    │   ├── immunization.py     # Vaccination history
    │   ├── medication.py       # Medication definitions
    │   └── medicationRequests.py # Prescriptions & Dosage "humanization"

```

## 🛠️ Code Description

### 1. Main Application (`main_app.py`)

This script is the **orchestrator** of the system. It uses **Streamlit** to render the frontend. Key responsibilities include:

* **FHIR Connection:** Connects to the FHIR Server using `fhirpy`.
* **Patient Selection:** Fetches and lists patients with a summary of their demographics.
* **Context Generation:** Orchestrates the retrieval of all clinical resources using the classes in `resources/` and generates the prompt for the LLM.
* **LLM Integration:** Loads `Bio-Medical-Llama-3` via `HuggingFace` transformers pipeline.
* **Chat Interface:** Manages the chat history and session state.
* **CDA Generation:** Converts the AI response into a valid XML CDA document and uploads it to the server.

### 2. Resource Wrappers (`resources/`)

To ensure clean code and maintainability, we implemented a **Wrapper Pattern**. Each FHIR resource has a dedicated Python class (e.g., `AppPatient`, `AppCondition`) that:

* Parses the raw JSON from the FHIR server.
* Validates data using `fhir.resources`.
* Exposes properties for easy access (e.g., `condition.clinical_status`).
* **`to_prompt_string()`**: A specialized method in every class that formats the resource data into a clean, text-based string optimized for LLM ingestion.

**Key Modules:**

* **`administration.patient`**: The core class. It contains the `generate_clinical_context()` method which aggregates all other resources to build the "Patient Clinical Summary".