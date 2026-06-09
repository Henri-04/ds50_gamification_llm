# Projet DS50 : IA Générative et Gamification

## Description

Système d'IA générative qui recommande des stratégies de **gamification pédagogique**
personnalisées à un enseignant. Le système s'appuie sur une **ontologie** (graphe de
connaissances OWL/RDF) pour ancrer ses propositions dans des faits réels (leçons,
ressources, profils d'apprenants, objectifs), et sur des **LLM** pour interpréter la
question, requêter le graphe et générer une ressource concrète.

## Architecture

Pipeline orchestré avec **LangGraph**, avec un **routage d'intention** en entrée :
selon la question, on recommande soit une **ressource** gamifiée, soit des
**personnes** (mentors / collègues au profil proche).

```
                          ┌─ (personnes) ─> Recommandation de profs ─────────────> fin
  Détection d'intention ──┤
                          └─ (ressource) ─> Agent 1 ─> Agent 2 ─> Bridge ─> Agent 3 ─> fin
                                            (ontologie)(SPARQL) (structure)(génération)
```

| Étape | Rôle | Techno |
|-------|------|--------|
| **Intention** | Classe la question (déterministe, mots-clés) : `people` (recommander des profs) ou `resource` (défaut). | — |
| **Recommandation de personnes** | Propose des mentors potentiels et des pairs au profil similaire, à partir des relations **déjà inférées** dans l'ontologie (`potentialMentorOf`, `hasSimilarProfile`, `moreExpertThan`…). 100 % SPARQL, aucun LLM. | `rdflib` |
| **Agent 1** | Explore l'ontologie OWL et produit une taxonomie épurée (`taxonomy_for_agent_2.json`) : extraction déterministe + 1 appel LLM de curation, avec repli sans LLM. | `owlready2`, Groq |
| **Agent 2** | Traduit la question (langage naturel) en requête **SPARQL**, l'exécute sur l'ontologie et renvoie les données réelles. Boucle de retry bornée si la requête échoue. | `rdflib`, Groq |
| **Bridge** | Structure la sortie d'Agent 2 en champs exploitables (profil apprenant, objectifs, élément de jeu…). Repli sur valeurs par défaut si le LLM renvoie un JSON invalide. | Groq |
| **Agent 3** | Génère la ressource gamifiée finale (Markdown) prête à l'emploi. | NVIDIA |

> La branche « personnes » est **purement déterministe** (SPARQL sur les relations
> inférées) : elle ne dépend d'aucune clé API ni d'aucun paquet LLM.

> L'ontologie est interrogée **en mémoire via rdflib** — aucun serveur Neo4j n'est
> nécessaire pour faire tourner l'application. Un guide d'import vers Neo4j existe à
> titre optionnel/exploratoire : [ontologies/IMPORT_OWL_NEO4J.md](ontologies/IMPORT_OWL_NEO4J.md).

## Stack technique

- **Interfaces** : application web **Streamlit** (`app.py`) ou ligne de commande (`src/main.py`)
- **Orchestration** : LangGraph / LangChain
- **LLM** : Groq (Agents 1, 2, Bridge) et NVIDIA (Agent 3) — modèles configurables
- **Ontologie** : OWL/RDF interrogée par SPARQL via `rdflib`
- **Modélisation** : Protégé (OWL/RDF)

## Structure du dépôt

```
ds50_gamification_llm/
├── app.py                      # Interface web Streamlit
├── requirements.txt
├── .env.example                # Modèle de configuration (clés API)
├── pytest.ini
├── taxonomy_for_agent_2.json   # Taxonomie produite par Agent 1 (cache)
├── ontologies/
│   ├── TGC_working-2026-06-05.owl  # Ontologie enrichie (SWRL matérialisées) — utilisée par le pipeline
│   ├── TGC_original.owl            # Version d'origine (sans relations entre profs)
│   └── IMPORT_OWL_NEO4J.md         # Import optionnel vers Neo4j
├── src/
│   ├── config.py               # Config centralisée (modèles LLM, défauts)
│   ├── main.py                 # Point d'entrée CLI interactif
│   ├── pipeline.py             # Logique partagée CLI ↔ interface (sélection + run)
│   ├── reason.py               # Raisonneur Pellet → régénère TGC_inferred.owl
│   ├── agent/
│   │   ├── intent.py           # Détection d'intention (people / resource)
│   │   ├── people.py           # Recommandation de personnes (mentors / pairs)
│   │   ├── agent1.py           # Curation d'ontologie
│   │   ├── agent2.py           # NL → SPARQL → recommandation
│   │   ├── agent3.py           # Génération de ressource
│   │   ├── nodes.py            # Nœuds LangGraph (intention, Bridge…)
│   │   ├── graph.py            # Assemblage de la pipeline (run_pipeline)
│   │   └── state.py            # AgentState (TypedDict)
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
- **Java 25+** — uniquement pour régénérer l'inférence (`python -m src.reason`).
  Pas nécessaire pour lancer l'app si `TGC_inferred.owl` est déjà présent.

### 2. Cloner et installer

```bash
git clone https://github.com/Henri-04/ds50_gamification_llm.git
cd ds50_gamification_llm

python -m venv .venv
# Windows :
.venv\Scripts\activate
# macOS/Linux :
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configuration (`.env` à la racine)

Copier le modèle, puis remplir les deux clés :

```bash
cp .env.example .env
```

```
GROQ_API_KEY=gsk_...      # https://console.groq.com/keys
NVIDIA_API_KEY=nvapi-...  # https://build.nvidia.com
```

Ce sont les **seules** variables requises. Les modèles LLM se règlent
directement dans `src/config.py`, **pas** dans `.env`. Le tracing LangSmith (`LANGCHAIN_*`) est
optionnel et désactivé par défaut.

## Lancement

### Interface web (Streamlit) — recommandé

```bash
streamlit run app.py
```
Choisir un **enseignant → un cours → une leçon**, puis poser ses questions dans le chat.
La ressource générée est sauvegardée dans `outputs_agent3/` et téléchargeable en `.md`.

### Ligne de commande (interactif)

```bash
python -m src.main
```
Même parcours (enseignant → cours → leçon → question) dans le terminal. Les étapes
des agents (`[Agent 1]`, `[Agent 2]`, `[Bridge]`…) s'affichent en temps réel dans la console.

### Autres commandes utiles

```bash
# Recommandation de personnes en direct (déterministe, sans LLM)
python -m src.agent.people Sara
```

La première exécution génère `taxonomy_for_agent_2.json` si absent (Agent 1).

### Régénérer l'inférence (relations entre enseignants)

La recommandation de **personnes** (mentors, pairs) s'appuie sur des relations
déduites par des **règles SWRL** : `potentialMentorOf`, `hasSimilarProfile`,
`moreExpertThan`… Elles sont matérialisées par le raisonneur **Pellet** (et non
HermiT, qui n'exécute pas les règles SWRL) dans `ontologies/TGC_inferred.owl`.

À relancer **après chaque modification de l'ontologie de travail** :

```bash
python -m src.reason     # raisonneur seul → réécrit TGC_inferred.owl
```

> ⚠ **Java 25+ requis** : les jars Pellet d'owlready2 ≥ 0.50 sont compilés pour
> Java 25 (sinon `UnsupportedClassVersionError`). macOS : `brew install --cask temurin`.
>
> Si `TGC_inferred.owl` est absent, le chargeur retombe sur l'ontologie de travail
> `TGC_working-…owl`, qui contient déjà ces relations (matérialisées via Protégé).

## Tests

```bash
pytest
```

Les tests couvrent l'exécution SPARQL, l'extraction d'ontologie (Agent 1), la
génération/retry SPARQL (Agent 2), le Bridge, la **détection d'intention** et la
**recommandation de personnes** — **sans nécessiter de clé API** (les appels LLM
sont mockés, et la branche « personnes » est 100 % SPARQL).

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
