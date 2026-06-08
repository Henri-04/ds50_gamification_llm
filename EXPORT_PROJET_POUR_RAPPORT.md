# Export du projet DS50 — pour rédaction du rapport

> Document de synthèse généré pour servir de matière première à la rédaction du
> rapport de projet. Il rassemble : la description fonctionnelle, l'architecture
> technique, le détail de chaque composant, l'historique de développement (Git)
> et la répartition du travail dans l'équipe.
>
> **Projet** : DS50 — IA Générative et Gamification pédagogique
> **Dépôt** : https://github.com/Henri-04/ds50_gamification_llm
> **Période** : 18 avril 2026 → 5 juin 2026
> **Export généré le** : 8 juin 2026

---

## 1. Présentation générale

### 1.1 Objectif

Système d'**IA générative** qui recommande des stratégies de **gamification
pédagogique personnalisées** à un enseignant. Le système s'appuie sur une
**ontologie** (graphe de connaissances OWL/RDF) pour **ancrer ses propositions
dans des faits réels** (leçons, ressources, profils d'apprenants, objectifs
pédagogiques), et sur des **LLM** pour interpréter la question de l'enseignant,
requêter le graphe, et générer une ressource pédagogique concrète et directement
utilisable.

Le verrou adressé : éviter qu'un LLM « hallucine » des recommandations
génériques. Ici, chaque proposition est tracée jusqu'à une donnée réelle de
l'ontologie (requête SPARQL + faits récupérés), et la ressource finale est
générée à partir de ces faits, pas inventée.

### 1.2 Proposition de valeur / originalité

- **Ancrage ontologique** : le LLM ne raisonne pas dans le vide, il requête un
  graphe de connaissances pédagogique structuré (ontologie TGC).
- **Anti-hallucination** : extraction déterministe en Python (les URIs sont la
  propriété du code, jamais du LLM) + flag explicite « ressource NON basée sur
  l'ontologie » quand aucune donnée n'est trouvée.
- **Traçabilité complète** : la ressource générée embarque la question, la
  requête SPARQL produite, les données trouvées et la décision de structuration
  (le « comment », pas seulement le « quoi »).
- **Économie de tokens** : pipeline conçu pour minimiser les appels et la taille
  des prompts (résumé compact de l'ontologie, curation en 1 appel sur noms seuls)
  — gestion explicite des limites de débit (rate-limit 429 de Groq).

---

## 2. Architecture technique

### 2.1 Vue d'ensemble

Pipeline orchestré avec **LangGraph**, avec un **routage d'intention** en entrée
qui aiguille vers deux usages : recommander une **ressource** gamifiée, ou
recommander des **personnes** (mentors / collègues).

```
                         ┌─ (personnes) ─> Reco. de profs (SPARQL) ───────────────────> fin
  Détection d'intention ─┤
                         └─ (ressource) ─> Agent 1 ─> Agent 2 ─> Bridge ─> Agent 3 ───> fin
                                           owlready2   rdflib     Groq      NVIDIA
                                           + Groq      + Groq
```

| Étape | Rôle | Techno | LLM |
|-------|------|--------|-----|
| **Agent 1** | Explore l'ontologie OWL et produit une taxonomie épurée (`taxonomy_for_agent_2.json`) : extraction déterministe + 1 appel LLM de curation, avec repli sans LLM. Lance aussi le raisonneur (règles SWRL). | `owlready2` | Groq (`openai/gpt-oss-120b`) |
| **Agent 2** | Traduit la question (langage naturel) en requête **SPARQL**, l'exécute sur l'ontologie, renvoie les données réelles. Boucle de retry bornée si la requête échoue ou est vide. Récupère aussi des « faits riches » déterministes sur la leçon. | `rdflib` | Groq (`llama-3.3-70b-versatile`) |
| **Bridge** | Structure la sortie d'Agent 2 en champs exploitables (profil apprenant, objectifs, élément de jeu…). Repli sur valeurs par défaut si le JSON LLM est invalide. | — | Groq (`llama-3.3-70b-versatile`) |
| **Agent 3** | Génère la ressource gamifiée finale (Markdown) prête à l'emploi, ancrée sur les faits de l'ontologie. | — | NVIDIA (`openai/gpt-oss-120b`) |

> L'ontologie est interrogée **en mémoire via rdflib** — aucun serveur Neo4j
> n'est nécessaire pour faire tourner l'application. Un guide d'import vers Neo4j
> existe à titre optionnel/exploratoire.

### 2.2 État partagé (LangGraph `AgentState`)

Chaque nœud reçoit et enrichit un `TypedDict` partagé. Champs principaux :

- **Entrée** : `user_input`, `teacher`, `course`, `lesson`
- **Agent 2** : `ontology_summary`, `sparql_query`, `query_results`, `attempts`,
  `recommendation`, `ontology_facts`
- **Bridge** : `learner_profile`, `pedagogical_objective`, `behavioural_objective`,
  `recommended_game_element`, `recommended_resource_type`
- **Agent 3** : `generated_resource`, `final_answer`

### 2.3 Stack technique

- **Interface** : ligne de commande (CLI / terminal)
- **Orchestration** : LangGraph 1.1.9 / LangChain 1.2.15
- **LLM** : Groq (Agents 1, 2, Bridge) et NVIDIA (Agent 3) — modèles configurables
- **Ontologie** : OWL/RDF, interrogée par SPARQL via `rdflib` 7.6.0 ;
  manipulation/raisonnement via `owlready2` 0.50 (raisonneur HermiT, Java requis)
- **Modélisation** : Protégé (OWL/RDF)
- **Tests** : `pytest` 8.3.4 (appels LLM mockés, pas de clé API requise)

---

## 3. Détail des composants

### 3.1 Agent 1 — Explorateur / curateur d'ontologie (`src/agent/agent1.py`)

Produit `taxonomy_for_agent_2.json` : un fichier permettant à l'Agent 2 (qui ne
connaît PAS le `.owl`) de requêter proprement le graphe (classes, URIs,
hiérarchie, relations domain/range, vocabulaire). Pipeline en **3 phases** conçu
pour être économe en tokens et anti-hallucination :

1. **Extraction déterministe (0 token)** — `owlready2` extrait TOUTE la structure
   (classes, object/data properties avec domain/range, individus groupés par
   classe). Les URIs sont produites par Python, jamais par le LLM.
2. **Curation LLM (1 seul appel, noms seuls)** — le LLM reçoit uniquement les
   *noms* (jamais une URI) et renvoie ceux pertinents pour le cas d'usage
   (recommandation de ressources gamifiées). Coût minime.
3. **Reconstruction + intégrité du graphe** — Python reconstruit le JSON final
   avec fermeture sur les ancêtres (la hiérarchie n'est jamais cassée) et ajout
   des classes référencées par les propriétés gardées.

Garde-fous : un set de **classes d'ancrage** (`ANCHOR_CLASSES`) toujours
conservées ; un **repli déterministe** (`fallback_keep`, basé sur les namespaces
pédagogiques `tgc`/`tco`) si le LLM est indisponible (clé manquante, rate-limit).

**Raisonneur SWRL** : `run_reasoner()` lance HermiT (via owlready2,
`infer_property_values=True`) une seule fois et sauvegarde l'ontologie enrichie
dans `ontologies/TGC_inferred.owl`. L'Agent 2 interroge ensuite cette version
enrichie. Nécessite Java.

### 3.2 Agent 2 — Recommandation NL → SPARQL (`src/agent/agent2.py`)

- **`generate_and_run()`** : traduit la question + résumé d'ontologie en requête
  SPARQL SELECT, l'exécute (`run_sparql`), et **réessaie (max 3 tentatives)** en
  renvoyant au LLM l'erreur de syntaxe ou le fait que la requête est vide.
- **Ancrage** (`_build_context`) : la requête est ancrée sur l'enseignant et la
  leçon réellement choisis (`tgc:<Teacher>`, `tgc:<Lesson>`), avec consignes pour
  garder la requête large (OPTIONAL sur types/titres, pas de filtre de langue).
- **`gather_ontology_facts()`** : récupération **déterministe** de faits riches
  sur la leçon (sujet, leçon préalable, profil enseignant, ressources et leurs
  éléments de jeu + objectifs). Ce texte sert de base solide à l'Agent 3 pour ne
  rien inventer.

### 3.3 Bridge — Structuration (`src/agent/nodes.py`, `node_bridge`)

Transforme la sortie libre de l'Agent 2 en **5 champs structurés** (JSON) pour
l'Agent 3 : `learner_profile`, `pedagogical_objective`, `behavioural_objective`
(valeur contrainte parmi une liste), `recommended_game_element`,
`recommended_resource_type`. **Robustesse** : si le LLM renvoie un JSON invalide
ou incomplet, chaque champ manquant est rempli par un repli sûr — l'Agent 3
dispose donc toujours de tous les champs.

### 3.4 Agent 3 — Génération de ressource (`src/agent/agent3.py`)

- Construit un prompt strict : « appuie-toi STRICTEMENT sur les FAITS DE
  L'ONTOLOGIE, n'invente AUCUN fait », et impose un **format Markdown** (titre,
  type, objectifs, élément de jeu, activité en étapes, feedback, justification).
- Appelle le LLM **NVIDIA** (`ChatNVIDIA`).
- **Flag honnête** : si l'Agent 2 n'a rien trouvé, la ressource est préfixée
  d'un avertissement « ⚠️ Ressource NON basée sur l'ontologie ».
- **`save_resource_to_file()`** : sauvegarde dans `outputs_agent3/` avec une
  section **Traçabilité** complète (question, requête SPARQL, données trouvées,
  faits, décision du Bridge).

### 3.5 Recommandation de personnes + routage d'intention (`src/agent/intent.py`, `src/agent/people.py`)

Au-delà des ressources, le système recommande aussi des **personnes** (autres
enseignants), en exploitant les relations entre profs **inférées par les règles
SWRL** (de Numidia) et matérialisées dans l'ontologie enrichie.

- **Détection d'intention** (`intent.py`) : classification déterministe par
  mots-clés (normalisation accents/casse) → `people` ou `resource` (défaut).
  Aucun LLM : robuste, instantané, testable sans clé API.
- **Recommandation** (`people.py`, **100 % SPARQL, sans LLM**) : pour un
  enseignant donné, interroge directement :
  - `tgc:potentialMentorOf` → **mentors potentiels** (plus experts, même domaine,
    même espace de travail) ;
  - `tgc:hasSimilarProfile` (repli `hasSimilarDomain`) → **pairs au profil
    similaire** (même player type + même domaine) ;
  puis enrichit chaque personne d'une fiche (nom, spécialité, niveau de
  gamification, style d'enseignement, compétences, leçons conçues) servant de
  **justification**.
- **Intégration LangGraph** : un nœud `classify_intent` route via une *conditional
  edge* vers `recommend_people` (branche courte, déterministe) ou vers le pipeline
  ressource historique.

> Cohérent avec la philosophie anti-hallucination du projet : l'identité des
> personnes recommandées vient **exclusivement** de l'ontologie, jamais du LLM.
> Les clients Groq/NVIDIA ont été rendus **paresseux** pour que cette branche
> fonctionne sans aucune dépendance LLM.

### 3.6 Outils & infrastructure

- **`src/tools/sparql_tools.py`** : charge l'ontologie OWL **une seule fois**
  (singleton module) ; utilise `TGC_inferred.owl` si le raisonneur a tourné,
  sinon l'ontologie enrichie `TGC_working-2026-06-05.owl`. `run_sparql()` injecte
  les PREFIX automatiquement, valide la syntaxe (`prepareQuery`, lève une exception
  explicite → utile pour le retry), et raccourcit les IRIs en noms locaux lisibles.
- **`src/config.py`** : configuration centralisée (modèles LLM, valeurs par
  défaut), `.env` chargé via `python-dotenv`.
- **`src/llm/groq_client.py`** / **`nvidia_client.py`** : clients LLM lazy
  (LangChain `ChatGroq` / `ChatNVIDIA`).
- **`src/agent/graph.py`** : assemblage de la pipeline (`create_pipeline`,
  `run_pipeline`) ; **`src/main.py`** : point d'entrée CLI.

### 3.7 Tests (`tests/`)

`pytest`, **sans clé API** (appels LLM mockés, branche personnes 100 % SPARQL) —
**37 tests au vert** :
- `test_sparql_tools.py` — exécution SPARQL
- `test_agent1.py` — extraction d'ontologie
- `test_agent2.py` — génération/retry SPARQL
- `test_bridge.py` — structuration + repli
- `test_intent.py` — détection d'intention (people / resource)
- `test_people.py` — recommandation de personnes (mentors / pairs)

---

## 4. Structure du dépôt (état final)

```
ds50_gamification_llm/
├── requirements.txt
├── pytest.ini
├── taxonomy_for_agent_2.json    # Taxonomie produite par Agent 1 (cache)
├── ontologies/
│   ├── TGC_working-2026-06-05.owl  # Ontologie enrichie (SWRL matérialisées, ~5233 triplets) — utilisée
│   ├── TGC_original.owl            # Version d'origine (~1859 triplets)
│   └── IMPORT_OWL_NEO4J.md         # Import optionnel vers Neo4j (n10s)
├── docs/                           # Doc des règles SWRL (Numidia)
├── src/
│   ├── config.py                # Config centralisée (modèles LLM, défauts)
│   ├── main.py                  # Point d'entrée CLI (principal)
│   ├── agent/
│   │   ├── intent.py            # Détection d'intention (people / resource)
│   │   ├── people.py            # Recommandation de personnes (mentors / pairs)
│   │   ├── agent1.py            # Curation d'ontologie + raisonneur
│   │   ├── agent2.py            # NL → SPARQL → recommandation
│   │   ├── agent3.py            # Génération de ressource
│   │   ├── nodes.py             # Nœuds LangGraph (intention, Bridge…)
│   │   ├── graph.py             # Assemblage de la pipeline (run_pipeline)
│   │   ├── state.py             # AgentState (TypedDict)
│   │   └── test_pipeline.py     # Démo interactive en terminal
│   ├── llm/
│   │   ├── groq_client.py       # Client Groq (lazy)
│   │   └── nvidia_client.py     # Client NVIDIA (lazy)
│   └── tools/
│       └── sparql_tools.py      # Chargement ontologie + exécution SPARQL
└── tests/                       # Tests pytest (sans clé API)
```

---

## 5. Installation & exécution

### Prérequis
- Python 3.10+, une clé API **Groq** et une clé API **NVIDIA**, Java (pour le raisonneur)

### Configuration (`.env`)
```
GROQ_API_KEY=gsk_...
NVIDIA_API_KEY=nvapi-...
# Optionnel : GROQ_MODEL, NVIDIA_MODEL, DEFAULT_TEACHER, DEFAULT_COURSE
```

### Lancement
```bash
# CLI sur une question (point d'entrée principal)
python -m src.main "Comment gamifier ma leçon sur l'héritage ?"

# Démo interactive en terminal (choix d'une leçon)
python -m src.agent.test_pipeline

# (Re)générer la taxonomie + lancer le raisonneur SWRL — à faire 1 fois
python -m src.agent.agent1

# Tests
pytest
```

### Modèles utilisés (par défaut, `src/config.py`)
- Agent 1 (curation) : Groq `openai/gpt-oss-120b`
- Agent 2 + Bridge : Groq `llama-3.3-70b-versatile`
- Agent 3 : NVIDIA `openai/gpt-oss-120b`

---

## 6. Historique de développement (Git)

### 6.1 Chronologie des jalons

| Date | Auteur | Jalon |
|------|--------|-------|
| 2026-04-18 | Henri Bost | Commit initial — préparation du terrain |
| 2026-04-22 | Swann | Pipeline RAG complet (collect, load, chunk, embed, retrieve) |
| 2026-04-26 | Numidia | Guide d'import OWL → Neo4j |
| 2026-04-27 | Swann | RAG : re-ranker cross-encoder + cosine + dedup |
| 2026-05-04 | Swann / Henri | Doc pipeline RAG ; merges RAG + Ontologie → main |
| 2026-05-07 | Swann | Use case « stress test » du système |
| 2026-05-10 | Numidia | Règles SWRL (topics de cours/leçons, objectifs comportementaux) |
| 2026-05-22 | Acil | 1ʳᵉ interface |
| 2026-05-27 | Swann | **Agent 2** : recommandation NL → SPARQL → exécution (`rdflib`) |
| 2026-05-31 | Numidia | **Agent 3** : génération de ressource gamifiée (ChatNVIDIA) |
| 2026-06-01 | Henri | **Agent 1** v1 (exploration OWL) + merges des 3 agents → main + pipeline test |
| 2026-06-01 | Henri | **Nettoyage majeur** : abandon de l'archi RAG/Neo4j, passage à l'archi ontologique (suppression des transcripts Coursera, modules RAG, clients Neo4j) |
| 2026-06-04 | Swann | **Pipeline ontologique fonctionnelle** : ancrage Agent 2, faits riches, reasoner HermiT, bascule sur ChatGroq, package Python propre, tests pytest |
| 2026-06-05 | Numidia | Règles SWRL pour recommandations enseignant (branche Ontology) |

### 6.2 Évolution de l'architecture (important pour le rapport)

Le projet a connu un **pivot d'architecture** notable :

1. **Phase 1 (avr.–mai)** : approche **RAG** (Retrieval-Augmented Generation) sur
   un corpus de transcripts du cours Coursera « Gamification » (collecte,
   chunking, embeddings, retrieval avec re-ranker cross-encoder) + exploration
   d'un import de l'ontologie vers **Neo4j**.
2. **Phase 2 (juin)** : **pivot vers une architecture purement ontologique**
   multi-agents. Le commit de nettoyage du 1ᵉʳ juin supprime ~10 900 lignes
   (transcripts, modules RAG, clients Neo4j) au profit de l'interrogation
   directe de l'ontologie en mémoire via SPARQL/rdflib. C'est l'architecture
   finale décrite dans ce document.

> Le développement s'est fait sur des **branches par agent/thème**
> (`RAG-Swann`, `Ontology-Numidia`, `agent2-swann`, `Agent3-Numidia`,
> `agent1_exploration_ontologie`, `interface`), mergées progressivement sur
> `main`.

### 6.3 Dernier commit (`HEAD`)

`c6408f3` — « Pipeline ontologique fonctionnelle : ancrage Agent 2, faits riches,
reasoner, ChatGroq » (2026-06-04), incluant : restructuration en package Python
propre, README aligné sur l'archi réelle, Agent 1 + raisonneur HermiT, Agent 2
ancré + faits riches, parsing JSON robuste du Bridge, Agent 3 ancré + flag « non
basée » + traçabilité, tests pytest. **~1225 insertions / 725 suppressions sur 25 fichiers.**

> État courant du dépôt : une modification non commitée sur
> `taxonomy_for_agent_2.json` (régénération de la taxonomie, fichier allégé).

---

## 7. Répartition du travail (par les commits)

| Contributeur | Commits | Contributions principales |
|--------------|---------|---------------------------|
| **Henri Bost** | 10 | Mise en place du projet, intégration/merges des branches sur `main`, Agent 1 v1, nettoyage et pivot d'architecture, pipeline de test |
| **Swann** | 10 | Pipeline RAG initial (collecte, embeddings, re-ranker), **Agent 2** (NL→SPARQL), outils SPARQL, ancrage + faits riches, raisonneur, bascule ChatGroq, restructuration en package + tests |
| **Numidia Nimha** | 9 | **Ontologie** et **règles SWRL** (inférence de topics, objectifs comportementaux, recommandations enseignant), guide import Neo4j, **Agent 3** (génération de ressource gamifiée NVIDIA) |
| **Acil** | 2 | Première interface |

*(Décompte `git shortlog` sur l'ensemble des branches.)*

---

## 8. Pistes pour le rapport

Éléments différenciants à mettre en avant :

- **Ancrage factuel anti-hallucination** : séparation stricte entre ce que produit
  Python (URIs, structure, faits déterministes) et ce que produit le LLM
  (sélection, génération de langage). Le LLM ne voit jamais une URI à l'Agent 1.
- **Robustesse en production** : replis déterministes à chaque étape (curation,
  Bridge), retry borné SPARQL, gestion explicite du rate-limit Groq.
- **Traçabilité / explicabilité** : chaque ressource embarque la requête SPARQL,
  les données trouvées et la chaîne de décision.
- **Raisonnement ontologique** : usage du raisonneur HermiT + règles SWRL pour
  enrichir le graphe avant interrogation.
- **Choix d'architecture documenté** : le pivot RAG → ontologie est un retour
  d'expérience intéressant à analyser (pourquoi l'ancrage ontologique structuré
  l'a emporté sur le RAG textuel pour ce cas d'usage de recommandation).

### Limites / perspectives possibles
- Interface en ligne de commande uniquement (une 1ʳᵉ interface a été ébauchée).
- Dépendance à deux fournisseurs LLM externes (Groq + NVIDIA) et à leurs quotas.
- Le raisonneur exige Java et un passage manuel ; la couverture des règles SWRL
  pourrait être étendue.
- Évaluation quantitative de la pertinence des recommandations non formalisée.
```
