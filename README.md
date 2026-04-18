# Projet DS50 : IA Générative et Gamification

## Description

Ce projet vise à concevoir un modèle d'intelligence artificielle générative fournissant des recommandations de gamification personnalisées pour les enseignants. Le système s'appuie sur un module conversationnel, un système de génération augmentée par la recherche (RAG) et un graphe de connaissances (ontologie) pour contextualiser les propositions selon les objectifs pédagogiques, la discipline et le profil des apprenants.

## Stack Technique

- **Interface utilisateur** : Streamlit
- **Orchestration IA** : LangChain / LangGraph
- **Modèles LLM** : API (Groq, Gemini, OpenAI) ou modèles locaux
- **Embeddings** : Hugging Face (local) ou via API
- **Bases de données** : Neo4j (Graphe / GraphRAG) et ChromaDB (Vecteurs)
- **Modélisation sémantique** : Protégé (OWL/RDF)

## Structure du répertoire

```
ds50_gamification_llm/
├── /ontologies          # Fichiers .owl ou .rdf de l'ontologie
├── /src                 # Code source Python (agents, graphe, utilitaires)
├── /data                # Documents d'entrée (cours au format texte/PDF)
├── app.py               # Point d'entrée de l'interface Streamlit
├── requirements.txt     # Liste des dépendances Python
└── README.md            # Documentation du projet
```

## Installation et démarrage

### 1. Prérequis

- Python 3.10 ou supérieur
- Neo4j Desktop (installé localement pour la base graphe)
- Une clé API valide pour le LLM choisi

### 2. Installation

```bash
# Cloner le dépôt
git clone https://github.com/Henri-04/ds50_gamification_llm.git
cd ds50_gamification_llm

# Créer et activer un environnement virtuel
python -m venv venv

# Sur Windows :
venv\Scripts\activate

# Sur macOS/Linux :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Configuration

Avant de lancer l'application, configurez vos clés API :

1. Créez un fichier `.env` à la racine du projet
2. Ajoutez vos variables d'environnement :
   ```
   GROQ_API_KEY=votre_clé_ici
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=votre_mot_de_passe
   ```

### 4. Lancement

```bash
# Démarrer l'application Streamlit
streamlit run app.py
```

L'application sera accessible à `http://localhost:8501`
