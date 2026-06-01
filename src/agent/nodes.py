"""Implémentation des 7 nœuds du graphe LangGraph."""
import json
import re

from src.llm.groq_client import call_llm
from src.tools.neo4j_tools import get_ontology_schema, query_ontology
from src.tools.rag_tools import (
    search_course_content,
    format_rag_results_for_prompt,
    format_ontology_rules_for_prompt,
    validate_rag_coverage,
)
from src.tools.validation import validate_against_ontology
from src.agent.state import AgentState


def analyze_query(state: AgentState) -> AgentState:
    """Nœud 1: Analyser la question pour identifier quelles règles chercher."""
    history_text = "\n".join(
        f"[{m['role']}]: {m['content']}" for m in state.get("conversation_history", [])
    ) or "[Première question]"

    schema = get_ontology_schema()

    prompt_text = f"""
Tu es un expert en pédagogie et gamification. Analyse la question utilisateur.

Contexte de l'ontologie:
{schema}

Historique:
{history_text}

Question: {state["current_query"]}

Identifie les concepts clés et construis les requêtes Cypher.
Réponds en JSON:
{{
  "reasoning_steps": ["étape 1", "étape 2"],
  "required_cypher_queries": ["MATCH (n:Concept) RETURN n"]
}}
"""

    try:
        response = call_llm([{"role": "user", "content": prompt_text}])
        response_text = response.choices[0].message.content
        
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        analysis = json.loads(json_match.group() if json_match else response_text)
        
        state["reasoning_chain"] = analysis.get("reasoning_steps", [response_text])
        state["required_queries"] = analysis.get("required_cypher_queries", ["MATCH (c:Concept) RETURN c LIMIT 5"])
    except Exception as e:
        state["reasoning_chain"] = [str(e)]
        state["required_queries"] = ["MATCH (c:Concept) RETURN c LIMIT 5"]

    return state


def fetch_ontology_rules(state: AgentState) -> AgentState:
    """Nœud 2: Exécuter les requêtes Cypher identifiées."""
    ontology_rules = []

    for query in state.get("required_queries", []):
        if not query.strip():
            continue
        try:
            results = query_ontology(query)
            ontology_rules.extend(results)
            state["reasoning_chain"].append(f"Cypher: {len(results)} résultats")
        except Exception as e:
            state["reasoning_chain"].append(f"Erreur Cypher: {str(e)}")

    state["ontology_rules"] = ontology_rules
    return state


def fetch_rag_content(state: AgentState) -> AgentState:
    """Nœud 3: Récupérer les passages du cours pertinents."""
    try:
        rag_results = search_course_content(state["current_query"], top_k=5)
        state["rag_results"] = rag_results
        
        has_coverage, avg_score = validate_rag_coverage(rag_results)
        state["reasoning_chain"].append(f"RAG: {len(rag_results)} passages (score: {avg_score:.2f})")
    except Exception as e:
        state["rag_results"] = []
        state["reasoning_chain"].append(f"Erreur RAG: {str(e)}")

    return state


def generate_draft(state: AgentState) -> AgentState:
    """Nœud 4: LLM génère un brouillon de recommandation."""
    ontology_text = format_ontology_rules_for_prompt(state.get("ontology_rules", []))
    rag_text = format_rag_results_for_prompt(state.get("rag_results", []))

    history_text = "\n".join(
        f"[{m['role']}]: {m['content']}"
        for m in state.get("conversation_history", [])
    ) or "[Première question]"

    prompt_text = f"""
Tu es expert en pédagogie et gamification.

{ontology_text}

{rag_text}

Historique:
{history_text}

Question: {state["current_query"]}

Génère une recommandation STRICTEMENT conforme aux règles de l'ontologie.
"""

    try:
        response = call_llm([{"role": "user", "content": prompt_text}])
        state["draft_recommendation"] = response.choices[0].message.content
        state["reasoning_chain"].append("Brouillon généré")
    except Exception as e:
        state["draft_recommendation"] = f"Erreur LLM: {str(e)}"

    return state


def validate_recommendation(state: AgentState) -> AgentState:
    """Nœud 5: Valider que la recommandation respecte les règles."""
    is_valid, errors = validate_against_ontology(
        state["draft_recommendation"],
        state.get("ontology_rules", []),
    )

    state["is_valid"] = is_valid
    state["validation_errors"] = errors

    if is_valid:
        state["reasoning_chain"].append("✓ Validation réussie")
    else:
        state["reasoning_chain"].append(f"✗ Validation échouée: {errors[0] if errors else 'Erreur inconnue'}")

    return state


def refine_or_clarify(state: AgentState) -> AgentState:
    """Nœud 6: Décider si on itère ou on finalise."""
    is_valid = state.get("is_valid", False)
    has_rag_data = len(state.get("rag_results", [])) > 0
    has_ontology_data = len(state.get("ontology_rules", [])) > 0
    retry_count = state.get("retry_count", 0)

    if is_valid:
        state["reasoning_chain"].append("→ Finalisation")
        return state

    if (not has_rag_data and not has_ontology_data) or retry_count >= 2:
        state["needs_clarification"] = True
        state["confidence"] = "low"
        state["reasoning_chain"].append("⚠ Clarification nécessaire")
        return state

    if has_rag_data or has_ontology_data:
        state["retry_count"] = retry_count + 1
        
        feedback = "\n".join(state.get("validation_errors", []))
        refine_prompt = f"""
Les éléments suivants ne sont pas conformes:
{feedback}

Révisez la recommandation pour être 100% conforme aux règles.
"""

        try:
            response = call_llm([
                {"role": "user", "content": refine_prompt},
                {"role": "user", "content": state["draft_recommendation"]}
            ])
            state["draft_recommendation"] = response.choices[0].message.content
            state["reasoning_chain"].append(f"Itération {state['retry_count']}: Affinée")
            
            is_valid, errors = validate_against_ontology(
                state["draft_recommendation"],
                state.get("ontology_rules", []),
            )
            state["is_valid"] = is_valid
            state["validation_errors"] = errors
        except Exception as e:
            state["reasoning_chain"].append(f"Erreur itération: {str(e)}")

    return state


def format_with_citations(state: AgentState) -> AgentState:
    """Nœud 7: Formater la recommandation avec citations sourcées."""
    if state.get("needs_clarification"):
        final_answer = f"""
Je n'ai pas suffisamment d'informations pour générer une recommandation fiable.

Erreurs: {', '.join(state.get('validation_errors', ['Données insuffisantes']))}

Pouvez-vous préciser:
1. Le contexte pédagogique (discipline, niveau)?
2. Les objectifs de gamification?
3. Les contraintes?

--- TRACE ---
{chr(10).join('→ ' + s for s in state.get('reasoning_chain', []))}
"""
        state["confidence"] = "low"
    else:
        recommendation = state.get("draft_recommendation", "")
        
        sources_ontology = "SOURCES ONTOLOGIE:\n"
        for rule in state.get("ontology_rules", [])[:3]:
            concept = rule.get("concept", "Unknown")
            rules = rule.get("rules", [])
            if rules:
                sources_ontology += f"• {concept}: {rules[0]}\n"

        sources_rag = "\nSOURCES COURS:\n"
        for result in state.get("rag_results", [])[:3]:
            if "error" not in result:
                source = result.get("source", "Unknown")
                score = result.get("score", 0)
                sources_rag += f"• {source} (confiance: {score:.0%})\n"

        reasoning_trace = "\nTRACE RAISONNEMENT:\n"
        for i, step in enumerate(state.get("reasoning_chain", []), 1):
            reasoning_trace += f"{i}. {step}\n"

        final_answer = f"""{recommendation}

{'━' * 60}
{sources_ontology}
{sources_rag}
{reasoning_trace}
"""
        state["confidence"] = "high" if len(state.get("rag_results", [])) > 0 else "medium"

    state["final_answer"] = final_answer
    return state
