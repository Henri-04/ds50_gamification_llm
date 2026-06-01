# Quick-Start : Nouveau Graphe LangGraph

## Installation

```bash
pip install -r requirements.txt
```

## Premier Test (30 secondes)

```python
from src.agent.graph import run_agent

result = run_agent('Comment gamifier un cours de mathématiques ?')
print(result['final_answer'])
```

## Voir la Traçabilité

```python
result = run_agent('Comment motiver les élèves ?')

print(f'Confiance: {result["confidence"]}')
print(f'Valide: {result["is_valid"]}')
print(f'Raisonnement:')
for step in result['reasoning_chain']:
    print(f'  → {step}')
```

## Multi-Tour

```python
# Tour 1
q1 = "Stratégie pour 2nde informatique"
r1 = run_agent(q1)

# Tour 2 avec contexte
history = [
    {"role": "user", "content": q1},
    {"role": "assistant", "content": r1['final_answer']}
]
r2 = run_agent("Ajoutez plus de compétition", conversation_history=history)
```

## Tests Complets

```bash
python3 src/main.py
```

Teste :
- Question simple
- Affinage multi-tour
- Raisonnement complexe
- Cas limites
- Workflow complet

## État Actuel

✅ Complet et testable (mock data)
✅ Prêt pour tests
🔄 Prêt pour intégration RAG + Neo4j réels

## Métadonnées de Qualité

```python
result = run_agent(...)

print(f"Confiance: {result['confidence']}")      # "high" / "medium" / "low"
print(f"Validée: {result['is_valid']}")           # bool
print(f"Clarification: {result['needs_clarification']}")  # bool
print(f"Règles utilisées: {result['ontology_rules_used']}")
print(f"Passages RAG: {result['rag_passages_used']}")
```

## Fichiers à Consulter

- **Architecture complète** → `LANGGRAPH_ARCHITECTURE.md`
- **Nœuds du graphe** → `src/agent/nodes.py`
- **État du système** → `src/agent/state.py`
- **Validation** → `src/tools/validation.py`

## Dépannage

**Error: langgraph not found**
```bash
pip install langgraph>=0.2.0
```

**Exécuter depuis la bonne racine**
```bash
cd /Users/henribost/Documents/Cours/Info\ 4\ -\ Data\ Science\ /DS50\ -\ Projet/code/ds50_gamification_llm
python3 src/main.py
```

**Mock data au lieu de vraies données**
C'est normal et attendu. Les données réelles seront intégrées quand RAG + Neo4j seront prêts.
