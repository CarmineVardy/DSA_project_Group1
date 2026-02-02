import os
import sys
from dotenv import load_dotenv
from fhirpy import SyncFHIRClient

def clean_patient_docs():
    # 1. Carica l'ambiente
    load_dotenv()
    server_url = os.getenv("SERVER_URL")
    
    if not server_url:
        print("❌ ERRORE: Variabile SERVER_URL non trovata nel file .env")
        return

    try:
        client = SyncFHIRClient(server_url)
        print(f"✅ Connesso al server: {server_url}")
    except Exception as e:
        print(f"❌ Errore di connessione: {e}")
        return

    # 2. Chiedi l'ID del Paziente
    print("\n--- PULIZIA DOCUMENTI AI ---")
    pid = input("Inserisci l'ID del Paziente da ripulire (es. 592913): ").strip()
    
    if not pid:
        print("Operazione annullata.")
        return

    print(f"\n🔍 Ricerca DocumentReference per il paziente {pid}...")

    try:
        # Scarica tutti i documenti del paziente
        docs = client.resources('DocumentReference').search(subject=f'Patient/{pid}').fetch_all()
    except Exception as e:
        print(f"❌ Errore durante la ricerca: {e}")
        return

    if not docs:
        print("⚠️  Nessun documento trovato per questo paziente.")
        return

    print(f"📄 Trovati {len(docs)} documenti totali. Analisi in corso...\n")

    deleted_count = 0
    skipped_count = 0

    # 3. Ciclo di eliminazione selettiva
    for doc in docs:
        doc_id = doc.id
        
        # Recupera il titolo/descrizione per capire se è nostro
        # Controlliamo sia il 'description' che il 'type.text' per sicurezza
        description = doc.get('description', 'Nessun Titolo')
        doc_type_text = doc.get('type', {}).get('text', '')
        
        # CRITERIO DI ELIMINAZIONE:
        # Cancella se il tipo è "AI Consultation Note" OPPURE se il titolo inizia con "Consultation_"
        is_ai_doc = (doc_type_text == "AI Consultation Note") or (description.startswith("Consultation_"))

        if is_ai_doc:
            print(f"🗑️  Eliminazione ID: {doc_id} | Titolo: {description}...", end=" ")
            try:
                doc.delete()
                print("✅ FATTO")
                deleted_count += 1
            except Exception as e:
                print(f"❌ ERRORE ({e})")
        else:
            print(f"🛡️  Saltato ID: {doc_id} | Tipo: {doc_type_text} (Non è generato dall'AI)")
            skipped_count += 1

    # 4. Riepilogo
    print("\n" + "="*30)
    print(f"🚀 OPERAZIONE COMPLETATA")
    print(f"🗑️  Eliminati: {deleted_count}")
    print(f"🛡️  Mantenuti: {skipped_count}")
    print("="*30)

if __name__ == "__main__":
    clean_patient_docs()