"""Outils wrapper pour le pipeline RAG."""
from rag.retriever import retrieve_with_scores, retrieve

#outils de rag pour l'agent
def search_course_content(query: str, top_k: int = 5) -> list[dict]:
    """Wrapper de retrieve_with_scores() pour le graphe LangGraph."""
    try:
        results = retrieve_with_scores(query, top_k)
        return results
    except Exception as e:
        return [{"error": f"Erreur RAG: {str(e)}", "content": "", "source": ""}]

#je sais pas si c'est utile 
def format_rag_results_for_prompt(rag_results: list[dict]) -> str:
    """Formate les résultats RAG pour inclusion dans les prompts LLM."""
    if not rag_results:
        return "Aucun passage du cours trouvé."

    formatted = "PASSAGES DU COURS PERTINENTS:\n"
    for i, result in enumerate(rag_results, 1):
        if "error" in result:
            continue
        formatted += f"\n[{i}] Source: {result.get('source', 'Unknown')} (Score: {result.get('score', 0):.2f})\n"
        formatted += f"{result.get('content', '')}\n"

    return formatted

#je sais pas si c'est utile
def format_ontology_rules_for_prompt(ontology_rules: list[dict]) -> str:
    """Formate les règles d'ontologie pour inclusion dans les prompts LLM."""
    if not ontology_rules:
        return "Aucune règle d'ontologie disponible."

    formatted = "RÈGLES DE L'ONTOLOGIE (MUST FOLLOW):\n"
    for rule in ontology_rules:
        if "error" in rule:
            continue

        concept = rule.get("concept", "Unknown")
        definition = rule.get("definition", "")
        rules = rule.get("rules", [])

        formatted += f"\n### {concept}\n"
        if definition:
            formatted += f"Définition: {definition}\n"
        if rules:
            formatted += "Règles:\n"
            for r in rules:
                formatted += f"  • {r}\n"

    return formatted

#ancienne fonction mck pour les tests 
"""def _get_mock_rag_results(query: str, top_k: int = 5) -> list[dict]:
    
    mock_data = {
        "gamification": [
            {
                "content": "La gamification est l'application d'éléments de jeu à un contexte non-ludique. Elle utilise des mécaniques comme les points, badges, leaderboards et missions.",
                "source": "Module Gamification - Fondamentaux.pdf",
                "score": 0.95,
                "chunk_id": "chunk_001",
            },
            {
                "content": "Le feedback immédiat augmente significativement la rétention et la motivation. Les apprenants qui reçoivent un feedback rapide sont plus engagés.",
                "source": "Module Gamification - Feedback.pdf",
                "score": 0.88,
                "chunk_id": "chunk_002",
            },
            {
                "content": "Les stratégies de gamification efficaces combinent récompenses, progression visible, feedback rapide, et compétition modérée.",
                "source": "Module Gamification - Stratégies.pdf",
                "score": 0.85,
                "chunk_id": "chunk_003",
            },
        ],
        "generic": [
            {
                "content": "Dans le contexte de la pédagogie moderne, il est important de considérer les préférences individuelles des apprenants.",
                "source": "Guide Pédagogique General.pdf",
                "score": 0.70,
                "chunk_id": "chunk_005",
            },
        ],
    }

    if any(word in query.lower() for word in ["gamif", "jeu", "point", "badge"]):
        results = mock_data["gamification"]
    else:
        results = mock_data["generic"]

    return results[:top_k]"""

#je sais pas si c'est utile - à supprimer 
def validate_rag_coverage(rag_results: list[dict], min_coverage: float = 0.6) -> tuple[bool, float]:
    """Valide que le RAG a une couverture suffisante."""
    if not rag_results:
        return False, 0.0

    valid_results = [r for r in rag_results if "error" not in r]

    if not valid_results:
        return False, 0.0

    avg_score = sum(r.get("score", 0) for r in valid_results) / len(valid_results)
    has_coverage = avg_score >= min_coverage

    return has_coverage, avg_score