import os
import json
import base64
import streamlit as st
import torch
import transformers
import huggingface_hub
from fhirpy import SyncFHIRClient
from dotenv import load_dotenv
from datetime import datetime

# --- 1. CONFIGURAZIONE ---
load_dotenv()
SERVER_URL = os.getenv("SERVER_URL")
HF_TOKEN = os.getenv("HF_TOKEN")
HISTORY_FILE = "chat_history.json"

st.set_page_config(page_title="FHIR Chatbot - BioLlama", layout="wide")

# --- 2. GESTIONE JSON ---
def load_json_history():
    if not os.path.exists(HISTORY_FILE): return {}
    try:
        with open(HISTORY_FILE, "r") as f: return json.load(f)
    except: return {}

def save_json_history(history_dict):
    with open(HISTORY_FILE, "w") as f: json.dump(history_dict, f, indent=4)

if "history_per_patient" not in st.session_state:
    st.session_state.history_per_patient = load_json_history()

# --- 3. FUNZIONE CDA (SOLO SALVATAGGIO) ---
def save_cda_to_fhir(patient_id, title, content):
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        cda_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <title>{title}</title>
    <effectiveTime value="{timestamp}"/>
    <recordTarget><patientRole><id extension="{patient_id}"/></patientRole></recordTarget>
    <component><nonXMLBody><text mediaType="text/plain">{content}</text></nonXMLBody></component>
</ClinicalDocument>"""

        encoded_content = base64.b64encode(cda_xml.encode('utf-8')).decode('utf-8')

        doc_ref = {
            'resourceType': 'DocumentReference',
            'status': 'current',
            'type': {'text': 'AI Consultation Note'},
            'subject': {'reference': f'Patient/{patient_id}'},
            'date': datetime.now().isoformat(),
            'description': title,
            'content': [{'attachment': {'contentType': 'text/xml', 'data': encoded_content, 'title': f"{title}.xml"}}]
        }
        client.resource('DocumentReference', **doc_ref).save()
        return True
    except Exception as e:
        st.error(f"Errore caricamento CDA: {e}")
        return False

# --- 4. CARICAMENTO MODELLO ---
@st.cache_resource(show_spinner="Inizializzazione Dr. Llama...")
def load_llm():
    if not HF_TOKEN: return None
    huggingface_hub.login(HF_TOKEN)
    return transformers.pipeline(
        "text-generation", 
        model="ContactDoctor/Bio-Medical-Llama-3-8B", 
        model_kwargs={"dtype": torch.bfloat16, "low_cpu_mem_usage": True}, 
        device_map="auto"
    )

llm = load_llm()
client = SyncFHIRClient(SERVER_URL)

# --- 5. SIDEBAR (PULITA) ---
with st.sidebar:
    st.title("🏥 Informazioni Paziente")
    try:
        from resources.administration.patient import AppPatient
        # Carichiamo i pazienti per la selezione
        resources = client.resources('Patient').limit(20).fetch()
        p_dict = {AppPatient(r.serialize()).get_full_name(): r.serialize() for r in resources}
        
        scelta = st.selectbox("Seleziona Paziente:", options=list(p_dict.keys()))
        patient_data = p_dict[scelta]
        pid = patient_data.get('id')
        
        # MOSTRA SOLO INFO BASE
        st.divider()
        st.write(f"**ID FHIR:** `{pid}`")
        st.write(f"**Paziente:** {scelta}")
        st.divider()
        
        if st.button("🗑️ Reset Chat Locale"):
            st.session_state.history_per_patient[pid] = []
            save_json_history(st.session_state.history_per_patient)
            st.rerun()
            
    except Exception as e:
        st.error(f"Errore connessione FHIR: {e}")

# --- 6. CHAT ---
st.title("💬 Dr. Llama - Medical Assistant")

if 'pid' in locals() and llm:
    if pid not in st.session_state.history_per_patient:
        st.session_state.history_per_patient[pid] = []
    
    history = st.session_state.history_per_patient[pid]

    for i, msg in enumerate(history):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                with st.expander("💾 Salva come Documento CDA"):
                    title_input = st.text_input("Titolo documento:", key=f"t_{i}")
                    if st.button("Carica su Server", key=f"cda_{i}"):
                        if title_input:
                            if save_cda_to_fhir(pid, title_input, msg["content"]):
                                st.success("Documento CDA creato correttamente sul server!")
                        else:
                            st.warning("Inserisci un titolo.")

    if prompt := st.chat_input("Fai una domanda clinica..."):
        history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analisi in corso..."):
                sys_msg = f"You are a medical assistant for patient {scelta} (ID: {pid})."
                # Usiamo solo gli ultimi 3 messaggi per stabilità
                clean_history = [m for m in history[-3:] if "not a doctor" not in m["content"]]
                messages = [{"role": "system", "content": sys_msg}] + clean_history
                
                prompt_ids = llm.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                outputs = llm(prompt_ids, max_new_tokens=512, temperature=0.1, repetition_penalty=1.3, do_sample=True)
                response = outputs[0]["generated_text"][len(prompt_ids):].strip()
                
                st.markdown(response)
                history.append({"role": "assistant", "content": response})
                st.session_state.history_per_patient[pid] = history
                save_json_history(st.session_state.history_per_patient)
                st.rerun()
else:
    st.info("👈 Seleziona un paziente per iniziare.")