"""Test et démonstration du nouveau graphe LangGraph robuste."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.graph import run_agent

def test_simple_query():
    """Test 1: Question simple de gamification."""
    print("\n" + "=" * 80)
    print("TEST 1: Question simple")
    print("=" * 80)

    query = "Comment motiver les élèves avec la gamification ?"
    result = run_agent(query)

    print(f"\nQuestion: {query}")
    print(f"\nRéponse:\n{result['final_answer']}")
    print(f"\nConfidence: {result['confidence']}")
    print(f"Valid: {result['is_valid']}")


def test_multi_turn():
    """Test 2: Conversation multi-tour avec affinage."""
    print("\n" + "=" * 80)
    print("TEST 2: Conversation multi-tour (affinage itératif)")
    print("=" * 80)

    query1 = "Recommandez une stratégie de gamification pour une classe 2nde informatique"
    result1 = run_agent(query1)

    print(f"\n[Tour 1] Question: {query1}")
    print(f"Confiance: {result1['confidence']}")

    history = [
        {"role": "user", "content": query1},
        {"role": "assistant", "content": result1["final_answer"]},
    ]

    query2 = "Pouvez-vous modifier pour ajouter plus de compétition ?"
    result2 = run_agent(query2, conversation_history=history)

    print(f"\n[Tour 2] Question: {query2}")
    print(f"Confiance: {result2['confidence']}")


def test_complex_query():
    """Test 3: Question complexe nécessitant plusieurs requêtes Cypher."""
    print("\n" + "=" * 80)
    print("TEST 3: Question complexe (raisonnement itératif)")
    print("=" * 80)

    query = (
        "Je dois enseigner des mathématiques à des lycéens démotivés. "
        "Quelle combinaison de feedback et récompenses serait optimale ?"
    )
    result = run_agent(query)

    print(f"\nQuestion: {query}")
    print(f"\nConfiance: {result['confidence']}")
    print(f"Raisonnement:")
    for i, step in enumerate(result["reasoning_chain"], 1):
        print(f"  {i}. {step}")


def test_insufficient_data():
    """Test 4: Cas limite - données insuffisantes."""
    print("\n" + "=" * 80)
    print("TEST 4: Cas limite - données insuffisantes")
    print("=" * 80)

    query = "Qqqqqqq xyzabc gamification?"
    result = run_agent(query)

    print(f"\nQuestion: {query}")
    print(f"Needs clarification: {result['needs_clarification']}")
    print(f"Confidence: {result['confidence']}")


def demonstrate_workflow():
    """Démonstration complète du workflow."""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION COMPLÈTE: Workflow robuste et traçable")
    print("=" * 80)

    print("\n📖 SCÉNARIO: Enseignant en SVT cherche à gamifier")

    query = "Créez une stratégie de gamification pour l'enseignement de la biologie"
    result = run_agent(query)

    print(f"\n📝 Question:\n   {query}")
    print(f"\n📊 Résultat:")
    print(f"   Confiance: {result['confidence']}")
    print(f"   Validée: {'✓' if result['is_valid'] else '✗'}")
    print(f"   Règles utilisées: {result['ontology_rules_used']}")
    print(f"   Passages cours: {result['rag_passages_used']}")


if __name__ == "__main__":


    print("TEST DU PIPELINE ")
    print("=" * 80)
    test_simple_query()

"""
    try:
        test_simple_query()
        test_multi_turn()
        test_complex_query()
        test_insufficient_data()
        demonstrate_workflow()

        print("\n" + "=" * 80)
        print("✓ TOUS LES TESTS COMPLÉTÉS")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
"""