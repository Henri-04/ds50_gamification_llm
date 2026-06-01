from dotenv import load_dotenv
from groq import Groq

#Chargement des variables d'environnement
load_dotenv()

# Initialisation du client
client = Groq()

def call_llm(messages):
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.2,
    )

#test de la connexion avec le llm
if __name__ =="__main__" : 

    messages=[
                {
                    "role": "user",
                    "content": "Bonjour !",
                }
            ]

    print(call_llm(messages))
