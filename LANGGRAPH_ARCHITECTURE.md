# Architecture LangGraph Robuste - Documentation Complète

## Vue d'ensemble

Le nouveau graphe LangGraph implémente une architecture **robuste, traçable et validée** pour générer des recommandations de gamification.

## 7 Nœuds du Graphe

```
START
  ↓
[1. analyze_query]          Identifier concepts clés et requêtes Cypher
  ↓
[2. fetch_ontology_rules]   Exécuter requêtes Cypher itérativement
  ↓
[3. fetch_rag_content]      Récupérer passages pertinents du cours
  ↓
[4. generate_draft]         LLM génère brouillon de recommandation
  ↓
[5. validate_recommendation] Valide 100% conformité aux règles
  ↓
[6. refine_or_clarify]      BOUCLE conditionnelle
  │                          ├─ Valide → [7]
  │                          ├─ Invalid + retry<2 → [4] (affinage)
  │                          └─ Données insuffisant → [7] + flag
  ↓
[7. format_with_citations]  Format final avec sources + trace
  ↓
END
```

## Fichiers Implémentés

- `src/agent/state.py` - AgentState enrichie
- `src/agent/prompts.py` - Prompts structurés
- `src/agent/nodes.py` - 7 nœuds (242 lignes)
- `src/agent/graph.py` - Orchestration LangGraph (97 lignes)
- `src/tools/validation.py` - Validation stricte
- `src/tools/neo4j_tools.py` - Interface Neo4j + mock (103 lignes)
- `src/tools/rag_tools.py` - Wrapper RAG (107 lignes)
- `src/main.py` - Tests complets (114 lignes)

## Utilisation Simple

```python
from src.agent.graph import run_agent

# Une question
result = run_agent("Comment motiver les élèves ?")
print(result['final_answer'])
print(f"Confiance: {result['confidence']}")
```

## Multi-Tour

```python
# Tour 1
r1 = run_agent("Stratégie pour 2nde")

# Tour 2 avec contexte
history = [
    {"role": "user", "content": "Stratégie..."},
    {"role": "assistant", "content": r1["final_answer"]}
]
r2 = run_agent("Ajoutez plus de compétition", conversation_history=history)
```

## Traçabilité Complète

```python
result = run_agent("Quelle est l'importance du feedback ?")

print(f"Raisonnement:\n{chr(10).join(result['reasoning_chain'])}")
print(f"Validée: {result['is_valid']}")
print(f"Ontologie: {result['ontology_rules_used']} règles")
print(f"RAG: {result['rag_passages_used']} passages")
```

## Garanties d'Architecture

✓ **Robustesse** : Validation stricte (pas d'hallucinations)
✓ **Explicabilité** : Traçabilité complète + citations
✓ **Raisonnement itératif** : Requêtes Cypher adaptatives
✓ **Multi-tour** : Affinage itératif 2-3 tours
✓ **Cas limites** : Flag needs_clarification

## Performance

- 3-5 appels LLM typiquement
- Max 2 itérations de validation
- Mock data pour tests sans dépendances externes

## Intégration Future

Quand le RAG sera prêt :
```python
# src/tools/rag_tools.py ligne 13
from src.rag.retriever import retrieve_with_scores
return retrieve_with_scores(query, top_k=top_k)
```

Quand Neo4j sera prêt :
```python
# src/tools/neo4j_tools.py ligne 35
from neo4j import GraphDatabase
driver = GraphDatabase.driver(NEO4J_URI, auth=(user, pwd))
```

## Tests

```bash
python3 src/main.py
```

Teste :
- Question simple
- Multi-tour
- Cas complexe
- Données insuffisantes
- Workflow complet
