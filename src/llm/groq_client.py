from dotenv import load_dotenv
from groq import Groq

#Chargement des variables d'environnement
load_dotenv()

# Initialisation du client
client = Groq()

def call_llm(messages):
    return client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.2,
    )