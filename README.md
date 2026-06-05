# Projet DS50 : IA Générative et Gamification

## Description

Système d'IA générative qui recommande des stratégies de **gamification pédagogique**
personnalisées à un enseignant. Le système s'appuie sur une **ontologie** (graphe de
connaissances OWL/RDF) pour ancrer ses propositions dans des faits réels (leçons,
ressources, profils d'apprenants, objectifs), et sur des **LLM** pour interpréter la
question, requêter le graphe et générer une ressource concrète.

## Architecture

Pipeline orchestré avec **LangGraph** en 4 étapes :

```
Agent 1 ──> Agent 2 ──> Bridge ──> Agent 3
(ontologie) (SPARQL)  (structure) (génération)
```

| Étape | Rôle | Techno |
|-------|------|--------|
| **Agent 1** | Explore l'ontologie OWL et produit une taxonomie épurée (`taxonomy_for_agent_2.json`) : extraction déterministe + 1 appel LLM de curation, avec repli sans LLM. | `owlready2`, Groq |
| **Agent 2** | Traduit la question (langage naturel) en requête **SPARQL**, l'exécute sur l'ontologie et renvoie les données réelles. Boucle de retry bornée si la requête échoue. | `rdflib`, Groq |
| **Bridge** | Structure la sortie d'Agent 2 en champs exploitables (profil apprenant, objectifs, élément de jeu…). Repli sur valeurs par défaut si le LLM renvoie un JSON invalide. | Groq |
| **Agent 3** | Génère la ressource gamifiée finale (Markdown) prête à l'emploi. | NVIDIA |

> L'ontologie est interrogée **en mémoire via rdflib** — aucun serveur Neo4j n'est
> nécessaire pour faire tourner l'application. Un guide d'import vers Neo4j existe à
> titre optionnel/exploratoire : [ontologies/IMPORT_OWL_NEO4J.md](ontologies/IMPORT_OWL_NEO4J.md).

## Stack technique

- **Interface** : ligne de commande (CLI / terminal)
- **Orchestration** : LangGraph / LangChain
- **LLM** : Groq (Agents 1, 2, Bridge) et NVIDIA (Agent 3) — modèles configurables
- **Ontologie** : OWL/RDF interrogée par SPARQL via `rdflib`
- **Modélisation** : Protégé (OWL/RDF)

## Structure du dépôt

```
ds50_gamification_llm/
├── requirements.txt
├── pytest.ini
├── taxonomy_for_agent_2.json   # Taxonomie produite par Agent 1 (cache)
├── ontologies/
│   ├── TGC3March2026.owl        # Ontologie de gamification pédagogique
│   └── IMPORT_OWL_NEO4J.md      # Import optionnel vers Neo4j
├── src/
│   ├── config.py               # Config centralisée (modèles LLM, défauts)
│   ├── logging_config.py
│   ├── main.py                 # Point d'entrée CLI (principal)
│   ├── agent/
│   │   ├── agent1.py           # Curation d'ontologie
│   │   ├── agent2.py           # NL → SPARQL → recommandation
│   │   ├── agent3.py           # Génération de ressource
│   │   ├── nodes.py            # Nœuds LangGraph (dont le Bridge)
│   │   ├── graph.py            # Assemblage de la pipeline (run_pipeline)
│   │   ├── state.py            # AgentState (TypedDict)
│   │   └── test_pipeline.py    # Démo interactive en terminal
│   ├── llm/
│   │   ├── groq_client.py      # Client Groq (lazy)
│   │   └── nvidia_client.py    # Client NVIDIA (lazy)
│   └── tools/
│       └── sparql_tools.py     # Chargement ontologie + exécution SPARQL
└── tests/                      # Tests pytest (sans clé API)
```

## Installation

### 1. Prérequis
- Python 3.10+
- Une clé API **Groq** et une clé API **NVIDIA**

### 2. Cloner et installer

```bash
git clone https://github.com/Henri-04/ds50_gamification_llm.git
cd ds50_gamification_llm

python -m venv venv
# Windows :
venv\Scripts\activate
# macOS/Linux :
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configuration (`.env` à la racine)

```
GROQ_API_KEY=gsk_...
NVIDIA_API_KEY=nvapi-...        # créer sur https://build.nvidia.com
```

Variables optionnelles (surcharge des défauts de `src/config.py`) :

```
GROQ_MODEL=llama-3.3-70b-versatile
NVIDIA_MODEL=openai/gpt-oss-120b
DEFAULT_TEACHER=Sara
DEFAULT_COURSE=ObjectOrientedProgramming
```

> Les clés `NEO4J_*` ne sont pas requises (Neo4j n'est pas utilisé par le code).

## Lancement

```bash
# CLI sur une question (point d'entrée principal)
python -m src.main "Comment gamifier ma leçon sur l'héritage ?"

# Démo interactive en terminal (choix d'une leçon)
python -m src.agent.test_pipeline

# (Re)générer la taxonomie + lancer le raisonneur (règles SWRL) — à faire 1 fois
python -m src.agent.agent1
```

> Le raisonneur (HermiT, via owlready2) déduit des faits et écrit `ontologies/TGC_inferred.owl`.
> Il tourne **une seule fois** ; ensuite l'Agent 2 interroge l'ontologie enrichie. **Java requis.**

La première exécution génère `taxonomy_for_agent_2.json` si absent (Agent 1).

## Tests

```bash
pytest
```

Les tests couvrent l'exécution SPARQL, l'extraction d'ontologie (Agent 1), la
génération/retry SPARQL (Agent 2) et le Bridge — **sans nécessiter de clé API**
(les appels LLM sont mockés).

## Utiliser la pipeline depuis un autre module

```python
from src.agent.graph import run_pipeline

result = run_pipeline(
    "Comment motiver les élèves avec la gamification ?",
    teacher="Sara",
    lesson="Lesson4_Inheritance",
)
print(result["final_answer"])
```
