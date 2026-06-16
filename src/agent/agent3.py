"""
Agent 3 — génération de la ressource gamifiée (provider NVIDIA).

Lit le state enrichi par Agent 1 → Agent 2 → Bridge, construit un prompt et
demande au LLM NVIDIA de produire une ressource pédagogique directement
utilisable par l'enseignant. N'effectue PAS de recommandation (déjà faite par
l'Agent 2) : il met en forme et concrétise.
"""

import os
import time
from datetime import datetime
from textwrap import dedent
from typing import Optional

from langgraph.graph import END, StateGraph

from .state import AgentState
from ..llm.nvidia_client import get_llm
from ..tools.sparql_tools import active_ontology_path


# ============================================================
# Node LangGraph : génération de ressource
# ============================================================

def generate_resource(state: AgentState) -> AgentState:
    """
    Node principal de l'Agent 3.

    Lit le state, construit un prompt, appelle le LLM NVIDIA, puis place la
    ressource générée dans state["generated_resource"].
    """
    print("Agent 3 : préparation du prompt...")

    prompt = dedent(f"""
        Tu es l'Agent 3 d'un système d'aide à la gamification pédagogique.

        Ton rôle :
        Générer une ressource gamifiée personnalisée pour un enseignant.

        Attention :
        - Tu ne dois PAS faire la recommandation (déjà faite par un agent précédent).
        - Appuie-toi STRICTEMENT sur les FAITS DE L'ONTOLOGIE ci-dessous : réutilise
          les ressources, éléments de jeu et objectifs RÉELS qui y sont listés, et
          n'invente AUCUN fait sur l'ontologie.
        - Si une info manque, tu peux compléter pédagogiquement, sans contredire ces faits.

        {state.get("ontology_facts") or "(Aucun fait d'ontologie disponible.)"}

        Contexte enseignant :
        - Enseignant : {state.get("teacher", "inconnu")}
        - Cours : {state.get("course", "inconnu")}
        - Leçon : {state.get("lesson", "inconnue")}

        Profil apprenant :
        {state.get("learner_profile", "non précisé")}

        Objectifs :
        - Objectif pédagogique : {state.get("pedagogical_objective", "non précisé")}
        - Objectif comportemental / motivationnel : {state.get("behavioural_objective", "non précisé")}

        Élément de jeu recommandé : {state.get("recommended_game_element", "non précisé")}

        Génère une ressource directement utilisable par l'enseignant.

        Format attendu :

        # Titre

        ## Type de ressource

        ## Objectif pédagogique

        ## Objectif comportemental

        ## Élément de jeu utilisé

        ## Activité proposée

        ### Étape 1
        ### Étape 2
        ### Étape 3

        ## Feedback donné à l'apprenant

        ## Utilisation par l'enseignant

        ## Justification

        Réponds en français, de manière claire et concrète.
    """)

    print("Agent 3 : appel du modèle NVIDIA...")
    start = time.perf_counter()
    response = get_llm().invoke(prompt)
    print(f"Agent 3 : génération terminée en {time.perf_counter() - start:.2f} s")

    texte = response.content
    # Si l'Agent 2 n'a rien trouvé, la ressource n'est PAS basée sur l'ontologie.
    if not state.get("ontology_facts") and not state.get("query_results"):
        texte = ("> ⚠️ Ressource NON basée sur l'ontologie "
                 "(l'Agent 2 n'a trouvé aucune donnée pour cette demande).\n\n") + texte

    state["generated_resource"] = texte
    return state


# ============================================================
# Traçabilité (partagée backend .md <-> interface)
# ============================================================

def _format_links(links: Optional[list]) -> str:
    """Liste à puces des triplets (sujet --predicat--> objet) traversés par Agent 2."""
    if not links:
        return "(aucun lien supplémentaire — l'Agent 2 n'a exploité que la requête SPARQL ci-dessus)"
    return "\n".join(f"- {l}" for l in links)


def _format_swrl_rules(cited: Optional[list]) -> str:
    """Détaille, pour chaque fait déduit utilisé, la ou les règles SWRL
    candidates et si leurs prémisses sont effectivement vérifiées.

    `cited` est une liste de {"rule": ..., "bindings": {var: individu},
    "verified": True/False/None} (cf. gather_ontology_facts/cite_swrl,
    agent2.py). Pour un même fait conclu, plusieurs règles peuvent avoir leurs
    prémisses vérifiées (ex: deux règles concluent toutes deux
    tgc:recommendedResource pour le même couple) : on les affiche toutes,
    avec le détail des prémisses (le « chemin » qui mène à la conclusion).
    """
    if not cited:
        return ("(aucune règle SWRL impliquée : les faits utilisés proviennent "
                "uniquement de propriétés assertées, pas de propriétés déduites)")

    # Regroupe par fait conclu (predicat + individus liés), pour comparer les
    # règles candidates entre elles quand elles concluent le même fait.
    groups: dict = {}
    for c in cited:
        rule = c["rule"]
        key = (rule["head_predicate"], tuple(sorted(c["bindings"].items())))
        groups.setdefault(key, []).append(c)

    out = []
    for (head_pred, bindings_items), entries in groups.items():
        bindings = dict(bindings_items)
        head_args = entries[0]["rule"].get("head_args", [])
        args_str = ", ".join(bindings.get(v, v) for v in head_args)
        out.append(f"- **tgc:{head_pred}({args_str})**")

        verified_labels = []
        for c in entries:
            rule, verified = c["rule"], c["verified"]
            if verified is True:
                statut = "✅ prémisses VÉRIFIÉES — cette règle explique bien ce fait"
                verified_labels.append(rule.get("label", head_pred))
            elif verified is False:
                statut = "❌ prémisses NON satisfaites — cette règle n'a PAS produit ce fait"
            else:
                statut = "ℹ️ non vérifiable (prémisses non structurées)"
            premisses = " ET ".join(rule.get("body_predicates", [])) or "(aucune prémisse)"
            out.append(f"  - **{rule.get('label', head_pred)}** : {premisses} → {statut}")
            if rule.get("comment"):
                out.append(f"    _{rule['comment']}_")

        if len(verified_labels) > 1:
            out.append(
                f"  -> {len(verified_labels)} règles ont leurs prémisses vérifiées pour ce "
                f"même fait ({', '.join(verified_labels)}) : elles y contribuent toutes."
            )
    return "\n".join(out)


def _format_bridge_output(state: AgentState) -> str:
    """Sortie structurée du Bridge LLM (les 5 champs transmis à Agent 3)."""
    if state.get("status") == "bridge_failed":
        return f"❌ échec du Bridge : {state.get('final_answer', '')}"
    champs = [
        ("learner_profile", "Profil apprenant"),
        ("pedagogical_objective", "Objectif pédagogique"),
        ("behavioural_objective", "Objectif comportemental"),
        ("recommended_game_element", "Élément de jeu recommandé"),
        ("recommended_resource_type", "Type de ressource"),
    ]
    return "\n".join(
        f"- **{label}** : {state.get(key) or '(non fourni)'}" for key, label in champs
    )


# ============================================================
# Justification du choix de la ressource gamifiée
# ============================================================

def _resource_objectives(resource: dict) -> list:
    """Objectifs liés à une ressource via ses éléments de jeu (relevantToObjective),
    sans doublons, dans l'ordre de découverte."""
    objectives = []
    for ge in resource.get("game_elements") or []:
        for o in ge.get("objectives") or []:
            if o not in objectives:
                objectives.append(o)
    return objectives


def _verified_fact(cited: Optional[list], head_predicate: str, domain_value: str,
                    range_value: Optional[str] = None) -> bool:
    """True s'il existe, dans `swrl_rules_cited`, une règle concluant
    `head_predicate(domain_value[, range_value])` dont les prémisses ont été
    vérifiées (cf. cite_swrl/verify_rule_premises, agent2.py)."""
    for c in cited or []:
        rule = c["rule"]
        if rule.get("head_predicate") != head_predicate or not c.get("verified"):
            continue
        head_args = rule.get("head_args", [])
        bindings = c.get("bindings", {})
        if len(head_args) > 0 and bindings.get(head_args[0]) != domain_value:
            continue
        if range_value is not None and len(head_args) > 1 and bindings.get(head_args[1]) != range_value:
            continue
        return True
    return False


def _select_resource(state: AgentState) -> Optional[dict]:
    """Choisit, parmi `state["candidate_resources"]`, la ressource à justifier.

    Priorité : recommandée par SWRL > gamifiée > alignée avec l'objectif
    comportemental du Bridge > possède au moins un élément de jeu.
    Retourne None si aucune ressource candidate."""
    candidates = state.get("candidate_resources") or []
    if not candidates:
        return None
    behavioural = state.get("behavioural_objective")

    def score(resource):
        return (
            resource.get("recommended_swrl", False),
            resource.get("is_gamified", False),
            bool(behavioural) and behavioural in _resource_objectives(resource),
            bool(resource.get("game_elements")),
        )

    return max(candidates, key=score)


def _mermaid_recommendation_path(state: AgentState, selected: Optional[dict]) -> str:
    """Graphe Mermaid (graph LR) : enseignant → leçon → ressource → objectif →
    recommandation SWRL. Flèches pleines = lien confirmé, pointillées = absent/
    non vérifié."""
    teacher = state.get("teacher", "?")
    lesson = state.get("lesson", "?")
    links = state.get("links_used") or []
    cited = state.get("swrl_rules_cited") or []

    lines = ["graph LR"]
    lines.append(f'    T["{teacher}"]')
    lines.append(f'    L["{lesson}"]')

    designs = f"tgc:{teacher} --tgc:designLesson--> tgc:{lesson}"
    lines.append(f'    T {"-->" if designs in links else "-.->"} |"designLesson"| L')

    if not selected:
        lines.append('    L -.-> |"aucune ressource identifiée"| MISS["non trouvé"]')
        return "\n".join(lines)

    res = selected["name"]
    lines.append(f'    R["{res}"]')

    reuse = f"tgc:{lesson} --tco:reuseResource--> tgc:{res}"
    lines.append(f'    L {"-->" if reuse in links else "-.->"} |"reuseResource"| R')

    # Objectif via designedWithObjective (SWRL vérifié en priorité, sinon premier disponible)
    objective = next(
        (o for o in _resource_objectives(selected)
         if _verified_fact(cited, "designedWithObjective", res, o)),
        (_resource_objectives(selected) or [None])[0],
    )
    if objective:
        verified_obj = _verified_fact(cited, "designedWithObjective", res, objective)
        badge = " ✅ SWRL" if verified_obj else " ❓"
        lines.append(f'    OBJ["{objective}"]')
        lines.append(f'    R {"-->" if verified_obj else "-.->"} |"designedWithObjective{badge}"| OBJ')

    rec_verified = selected.get("recommended_swrl") and _verified_fact(cited, "recommendedResource", teacher, res)
    badge_r = " ✅ SWRL" if rec_verified else " ❌"
    lines.append(f'    T {"-->" if rec_verified else "-.->"} |"recommendedResource{badge_r}"| R')

    return "\n".join(lines)


def _mermaid_game_element_path(state: AgentState, selected: Optional[dict]) -> str:
    """Graphe Mermaid (graph LR) : ressource → élément de jeu → objectif(s) →
    cohérence avec l'objectif comportemental choisi par le Bridge."""
    if not selected or not selected.get("game_elements"):
        return 'graph LR\n    X["non trouvé dans l\'ontologie"]'

    behavioural = state.get("behavioural_objective")
    cited = state.get("swrl_rules_cited") or []
    res = selected["name"]

    # Préfère l'élément aligné avec l'objectif comportemental du Bridge
    chosen = next(
        (ge for ge in selected["game_elements"]
         if behavioural and behavioural in (ge.get("objectives") or [])),
        selected["game_elements"][0],
    )
    element = chosen["name"]
    objectives = chosen.get("objectives") or []

    lines = ["graph LR"]
    lines.append(f'    R["{res}"]')
    lines.append(f'    GE["{element}"]')
    lines.append('    R --> |"containsGameElement"| GE')

    for i, o in enumerate(objectives):
        # Marque l'objectif aligné avec le Bridge avec un ✓ dans son label
        label = f"{o} ✓" if (behavioural and o == behavioural) else o
        lines.append(f'    O{i}["{label}"]')
        lines.append(f'    GE --> |"relevantToObjective"| O{i}')

    # designedWithObjective est une relation Resource → Objective (inférée par SWRL
    # à partir de containsGameElement + relevantToObjective) : elle part de R, pas de O.
    if behavioural and behavioural in objectives:
        idx = objectives.index(behavioural)
        verified = _verified_fact(cited, "designedWithObjective", res, behavioural)
        badge = "✅ SWRL" if verified else "⚠️ non vérifié"
        lines.append(f'    R --> |"designedWithObjective {badge}"| O{idx}')

    return "\n".join(lines)


def render_resource_choice_justification(state: AgentState) -> str:
    """Sous-section Markdown « Justification du choix de la ressource gamifiée »,
    intégrée dans build_traceability (séparée proprement de la trace pipeline).

    Deux graphes Mermaid dérivés uniquement de state["candidate_resources"],
    state["links_used"] et state["swrl_rules_cited"] — aucun fait inventé.
    """
    selected = _select_resource(state)

    parts = [
        "### Justification du choix de la ressource gamifiée",

        "**1. Chemin de recommandation**\n"
        "```mermaid\n" + _mermaid_recommendation_path(state, selected) + "\n```",

        "**2. Cohérence de l'élément de jeu**\n"
        "```mermaid\n" + _mermaid_game_element_path(state, selected) + "\n```",
    ]

    if selected is None:
        parts.append("_Aucune ressource candidate n'a été trouvée dans l'ontologie pour cette leçon._")

    return "\n\n".join(parts)


def build_traceability(state: AgentState) -> str:
    """Section « Traçabilité » en Markdown : reconstitue le raisonnement complet
    de la pipeline Agent 1 -> Agent 2 -> Bridge -> Agent 3, étape par étape.

    Source UNIQUE utilisée à la fois par le rapport .md (save_resource_to_file)
    et par l'interface (expander « Détails du raisonnement »), afin que le détail
    affiché soit strictement identique à la traçabilité des rapports backend.
    """
    sparql = state.get("sparql_query") or "(aucune)"
    facts = state.get("ontology_facts") or "(aucun)"
    swrl_rules = state.get("swrl_rules") or []
    tentatives = state.get("bridge_attempts")

    blocks = [
        "## Traçabilité",
        f"**Question:** {state.get('user_input', '')}",

        "### Étape 1 — Agent 1 : ontologie et règles SWRL",
        f"- Ontologie interrogée par l'Agent 2 : `{active_ontology_path().name}`\n"
        f"- Règles SWRL connues (extraites par l'Agent 1) : {len(swrl_rules)} "
        "— servent ci-dessous à vérifier quels faits déduits ont été utilisés.",

        "### Étape 2 — Agent 2 : requête SPARQL, faits et règles SWRL",
        "**Requête SPARQL générée par l'Agent 2 (= ce qu'il a décidé de chercher):**",
        f"```sparql\n{sparql}\n```",
        f"**Données trouvées dans l'ontologie:** {state.get('query_results')}",
        f"**Recommandation (résumé des données ci-dessus) :** {state.get('recommendation', '')}",
        "**Liens de l'ontologie exploités par l'Agent 2 (déterministe, en plus de la requête SPARQL ci-dessus) :**",
        _format_links(state.get("links_used")),
        "**Faits riches récupérés (déterministe) :**",
        f"```\n{facts}\n```",
        "**Règles SWRL impliquées dans ces faits déduits** "
        "(pour chaque fait déduit utilisé ci-dessus, on revérifie par requête SPARQL "
        "si les prémisses de chaque règle candidate sont satisfaites pour les individus "
        "concernés — si plusieurs règles sont vérifiées, elles contribuent toutes) :",
        _format_swrl_rules(state.get("swrl_rules_cited")),

        "### Étape 3 — Bridge LLM : interprétation pédagogique",
        "Entrée : la question, la leçon et les FAITS DE L'ONTOLOGIE de l'étape 2 ci-dessus"
        + (f" ({tentatives} tentative(s) jusqu'à un JSON valide)." if tentatives else ".")
        + " Sortie structurée transmise à l'Agent 3 :",
        _format_bridge_output(state),

        "### Étape 4 — Agent 3 : génération de la ressource",
        "Le prompt de l'Agent 3 reprend STRICTEMENT les FAITS DE L'ONTOLOGIE (étape 2) "
        "et la sortie du Bridge (étape 3) ci-dessus, plus le contexte enseignant / cours "
        "/ leçon ; la ressource générée à partir de ce prompt est jointe après cette section.",

        "---",
        render_resource_choice_justification(state),
    ]
    return "\n\n".join(blocks)


# ============================================================
# Sauvegarde du résultat dans un fichier
# ============================================================

def save_resource_to_file(state: AgentState, filename: Optional[str] = None) -> str:
    """Sauvegarde la ressource générée dans outputs_agent3/ et retourne le chemin."""
    output_dir = "outputs_agent3"
    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resource_{timestamp}.md"

    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Ressource générée par Agent 3\n\n")
        f.write(f"**Enseignant:** {state.get('teacher', '?')}\n")
        f.write(f"**Cours:** {state.get('course', '?')}\n")
        f.write(f"**Leçon:** {state.get('lesson', '?')}\n")
        f.write(f"**Élément de jeu:** {state.get('recommended_game_element', '?')}\n")
        f.write(f"**Date de génération:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Traçabilité : comment la recommandation a été obtenue (le "comment", pas juste le "quoi").
        # Même bloc que celui affiché dans l'interface (build_traceability).
        f.write("---\n\n")
        f.write(build_traceability(state))
        f.write("\n\n---\n\n")
        f.write(state.get("generated_resource", ""))

    return filepath


# ============================================================
# Construction du graph LangGraph (sous-graphe Agent 3)
# ============================================================

def build_agent3_graph():
    """Baseline minimale : generate_resource -> END."""
    workflow = StateGraph(AgentState)
    workflow.add_node("generate_resource", generate_resource)
    workflow.set_entry_point("generate_resource")
    workflow.add_edge("generate_resource", END)
    return workflow.compile()


# ============================================================
# Démo locale : python -m src.agent.agent3
# ============================================================

def _demo_state() -> AgentState:
    """State d'exemple (autonome) pour tester l'Agent 3 sans les agents amont."""
    return {
        "teacher": "Sara",
        "course": "Lesson1_JavaBasics",
        "lesson": "Java Constructors",
        "learner_profile": (
            "Apprenants débutants en programmation Java, "
            "profil Socializer, style de compréhension séquentiel."
        ),
        "pedagogical_objective": "Comprendre le rôle d'un constructeur dans une classe Java.",
        "behavioural_objective": "Motivation",
        "recommended_game_element": "Progress Bar",
        "recommended_resource_type": "Mini-exercice gamifié",
        "query_results": [
            {
                "source": "ontology",
                "gameElement": "Progress Bar",
                "relatedObjective": "Motivation",
            }
        ],
    }


def main() -> None:
    agent3 = build_agent3_graph()
    result = agent3.invoke(_demo_state())

    print("\n==============================")
    print("RESSOURCE GÉNÉRÉE PAR AGENT 3")
    print("==============================\n")
    print(result["generated_resource"])

    filepath = save_resource_to_file(result)
    print(f"\n✓ Fichier sauvegardé : {filepath}")


if __name__ == "__main__":
    main()
