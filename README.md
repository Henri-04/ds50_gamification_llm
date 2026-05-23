# Projet DS50 : IA Generative et Gamification

## Description

Systeme d'intelligence artificielle generative fournissant des recommandations de gamification personnalisees pour les enseignants. Le systeme s'appuie sur un module conversationnel, un pipeline RAG (Retrieval-Augmented Generation) et un graphe de connaissances (ontologie) pour contextualiser les propositions selon les objectifs pedagogiques, la discipline et le profil des apprenants.

## Stack Technique

- **Interface utilisateur** : Streamlit
- **Orchestration IA** : LangChain / LangGraph
- **Modeles LLM** : API (Groq, Gemini, OpenAI) ou modeles locaux
- **Embeddings** : Sentence-Transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **Base vectorielle** : ChromaDB (locale, sans serveur)
- **Base de graphe** : Neo4j (ontologie, regles SWRL)
- **Modelisation semantique** : Protege (OWL/RDF)

## Structure du repertoire

```
ds50_gamification_llm/
├── app.py                    # Point d'entree Streamlit 
├── requirements.txt          # Dependances Python
├── README.md
├── .env                      # Cles API (non versionne)
├── /data                     # Donnees de cours
│   ├── /coursera_gamification  # Contenu extrait via API Coursera
│   │   ├── transcript_*.txt    # Transcriptions des videos
│   │   └── supplement_*.txt    # Contenu des lectures
│   └── /cours_DS52             # PDF de cours supplementaires
├── /src                      # Code source
│   └── /rag                  # Pipeline RAG 
│       ├── __init__.py
│       ├── collect_coursera.py  # Collecte automatique via API Coursera
│       ├── loader.py            # Chargement des documents (TXT + PDF)
│       ├── chunker.py           # Decoupage en chunks (500 chars, overlap 50)
│       ├── embedder.py          # Vectorisation + stockage ChromaDB
│       └── retriever.py         # Recherche semantique (fonction retrieve())
├── /ontologies               # Fichiers .owl ou .rdf 
└── /chroma_db                # Base vectorielle generee (non versionnee)
```

## Installation et demarrage

### 1. Prerequis

- Python 3.10 ou superieur
- Neo4j Desktop (pour la base graphe)
- Une cle API valide pour le LLM choisi (Groq, OpenAI, etc.)

### 2. Cloner et installer

```bash
git clone https://github.com/Henri-04/ds50_gamification_llm.git
cd ds50_gamification_llm

# Creer et activer un environnement virtuel
python -m venv venv

# Windows :
venv\Scripts\activate

# macOS/Linux :
source venv/bin/activate

# Installer les dependances
pip install -r requirements.txt
```

### 3. Configuration

Creer un fichier `.env` a la racine :

```
GROQ_API_KEY=votre_cle_ici
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=votre_mot_de_passe
```

### 4. Pipeline RAG : collecte et indexation

Ces commandes collectent les donnees de cours et construisent la base vectorielle.
A executer une seule fois (ou quand les donnees changent).

```bash
# Collecter le contenu du cours Coursera (transcriptions + supplements)
python src/rag/collect_coursera.py

# Construire la base vectorielle (charge, decoupe, vectorise, stocke)
python src/rag/embedder.py
```

Verifier que tout fonctionne :

```bash
# Tester la recherche semantique
python src/rag/retriever.py
```

### 5. Lancement de l'application

```bash
streamlit run app.py
```

L'application sera accessible a `http://localhost:8501`

## Utilisation du RAG depuis un autre module

```python
from src.rag.retriever import retrieve

# Recherche semantique (fonctionne en francais et en anglais)
passages = retrieve("Comment motiver les eleves ?", top_k=3)
```
