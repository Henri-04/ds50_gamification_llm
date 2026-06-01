#Définition des états de l'agent
from typing import TypedDict, Optional, Any


class AgentState(TypedDict, total=False):
    # --- Champs existants (agent decide/tool/final) ---
    user_input: str
    decision: Optional[str]
    tool_result: Optional[str]
    final_answer: Optional[str]

    # --- Champs Agent 2 (Agent de recommandation : NLP -> SPARQL -> execute) ---
    # Resume brut produit par l'Agent 1 (blob opaque, interprete par le LLM).
    ontology_summary: Optional[str]
    # Derniere requete SPARQL generee par le LLM.
    sparql_query: Optional[str]
    # Resultats reels renvoyes par l'ontologie (liste de lignes).
    query_results: Optional[list[dict]]
    # Nombre de tentatives effectuees (boucle de retry).
    attempts: Optional[int]
    # Recommandation finale formatee a partir des donnees reelles.
    recommendation: Optional[str]
