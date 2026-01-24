import os
from dotenv import load_dotenv
load_dotenv()

import transformers 
import torch
import huggingface_hub

print("Logging to Hugging Face...")
# SOSTITUIRE 'hf_XXXXXXXXXXXXXXXX' CON IL TUO VERO TOKEN DI ACCESSO
token = os.getenv("HF_TOKEN")
if not token:
    print("ERRORE: HF_TOKEN not found.")
huggingface_hub.login(token)

print("Defining the model...")
# ID del modello LLM su Hugging Face
model_id = "ContactDoctor/Bio-Medical-Llama-3-8B"
# Setup del modello 
pipeline = transformers.pipeline(
	"text-generation", 
	model=model_id, 
	model_kwargs={"dtype": torch.bfloat16}, 
	device_map="auto", 
)

# Verifica della disponibilità di gpu
if torch.cuda.is_available():
    device = f"cuda:{torch.cuda.current_device()}"
else: 
    device = "cpu"
print(f"Loading the model {model_id} on device {device}")

print("Setting the prompt...")
# Definizione del prompt in formato chat (Llama-3 utilizza un formato specifico)
messages = [ 
	{
		"role": "system", 
		"content": "You are an expert trained on healthcare and biomedical domain!"
	}, 
	{
		"role": "user", 
		"content": "I'm a 35-year-old male and for the past few months, I've been experiencing fatigue, increased sensitivity to cold, and dry, itchy skin. What is the diagnosis here?"
	}, 
]
print("Instruction: ", messages[0]["content"])
print("Question: ", messages[1]["content"])

print("Setting the tokenizer...")
# Definizione della conversione dell'input in token ids
prompt = pipeline.tokenizer.apply_chat_template( 
	messages, 
	tokenize=False, 
	add_generation_prompt=True 
)
# Definizione dei token di terminazione per la risposta (<|eot_id|> è specifico per i modelli Llama-3)
terminators = [ 
	pipeline.tokenizer.eos_token_id, 
	pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>") 
]

print("Performing the inference...")
outputs = pipeline( 
	prompt, 
	max_new_tokens=256, 
	eos_token_id=terminators, 
	do_sample=True, 
	temperature=0.6, 
	top_p=0.9, 
) 

# Estrazione della risposta generata, escludendo il prompt iniziale
answer = outputs[0]["generated_text"][len(prompt):]
print("Answer: ", answer)
