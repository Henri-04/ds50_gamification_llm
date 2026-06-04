"""
Agent 2 — recommandation.

Traduit la question de l'enseignant en requête SPARQL, l'exécute sur l'ontologie
et renvoie les données trouvées. Une petite boucle de retry corrige la requête
si elle est invalide ou ne renvoie rien.
"""

import re

from ..llm.groq_client import call_llm
from ..tools.sparql_tools import run_sparql, PREFIXES

MAX_RETRIES = 3  # chaque tentative = 1 appel LLM (resume court -> peu de tokens)


_SYSTEM_PROMPT = f"""\
Tu es un generateur de requetes SPARQL pour une ontologie de gamification \
pedagogique (ontologie TGC).

A partir d'un resume de l'ontologie et d'une question, tu produis UNE requete \
SPARQL SELECT qui recupere les donnees reelles permettant de repondre.

Prefixes disponibles (deja declares, tu peux les utiliser directement) :
{PREFIXES}
Regles :
- Reponds UNIQUEMENT par la requete SPARQL, sans explication ni texte autour.
- N'invente aucune entite : utilise exactement les noms presents dans le resume.
- Garde la requete LARGE pour ne rien exclure : mets le type (a/rdf:type) et les
  attributs (titre, description) en OPTIONAL.
- N'utilise JAMAIS de FILTER sur la langue (lang()) : les libelles n'ont pas de tag.
"""


def _build_context(state):
    """Ancre la requête sur l'enseignant et la leçon réellement choisis."""
    teacher = state.get("teacher")
    lesson = state.get("lesson")
    course = state.get("course")
    parts = []
    if teacher:
        parts.append(f"- enseignant : tgc:{teacher}")
    if lesson:
        parts.append(f"- lecon : tgc:{lesson}")
    if course:
        parts.append(f"- cours : {course}")
    if not parts:
        return ""
    return (
        "Contexte — ANCRE ta requete sur ces individus EXACTS :\n" + "\n".join(parts) + "\n"
        "Pour les ressources d'une lecon, fais SIMPLE et LARGE :\n"
        "  tgc:<Lecon> tco:reuseResource ?res . OPTIONAL { ?res tgc:has_title ?title }\n"
        "Mets le type (tgc:GamifiedResource) en OPTIONAL, et PAS de FILTER de langue."
    )


def _build_messages(question, summary, feedback, context=""):
    user = f"Resume de l'ontologie :\n{summary}\n\n"
    if context:
        user += f"{context}\n\n"
    user += f"Question de l'enseignant :\n{question}"
    if feedback:
        user += f"\n\nLa tentative precedente a echoue : {feedback}\nCorrige la requete."
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def _extract_sparql(text):
    """Récupère la requête SPARQL dans la réponse du LLM (enlève le markdown)."""
    fenced = re.search(r"```(?:sparql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    match = re.search(r"(PREFIX|SELECT|ASK|CONSTRUCT)\b", text, re.IGNORECASE)
    if match:
        return text[match.start():].strip()
    return text.strip()


def _format_recommendation(question, rows):
    if not rows:
        return "Aucune donnee correspondante n'a ete trouvee dans l'ontologie pour cette demande."
    lines = [f"{len(rows)} resultat(s) trouve(s) dans l'ontologie :"]
    for row in rows:
        parts = [f"{k}={v}" for k, v in row.items() if v is not None]
        lines.append("  - " + ", ".join(parts))
    return "\n".join(lines)


def generate_and_run(question, summary, context="", max_retries=MAX_RETRIES):
    """Génère une requête SPARQL, l'exécute, et réessaie si invalide ou vide."""
    feedback = None
    last_query = ""
    last_rows = []
    for attempt in range(1, max_retries + 1):
        reponse = call_llm(_build_messages(question, summary, feedback, context))
        last_query = _extract_sparql(reponse)
        try:
            last_rows = run_sparql(last_query)
        except Exception as exc:  # requête invalide -> on renvoie l'erreur au LLM
            feedback = f"erreur de syntaxe SPARQL : {exc}"
            continue
        if last_rows:
            return {"sparql_query": last_query, "query_results": last_rows,
                    "attempts": attempt, "error": None}
        feedback = "la requete etait valide mais n'a renvoye aucun resultat."
    return {"sparql_query": last_query, "query_results": last_rows,
            "attempts": max_retries, "error": feedback}


def gather_ontology_facts(state):
    """
    Récupère de façon déterministe un maximum de faits réels sur la leçon choisie
    (ressources, éléments de jeu, objectifs, sujet, profil du prof). Ce texte sert
    de base solide à Agent 3 pour qu'il s'appuie sur l'ontologie, sans inventer.
    """
    lesson = state.get("lesson")
    teacher = state.get("teacher")
    if not lesson:
        return ""

    facts = []

    # Sujet et leçon préalable
    topics = run_sparql(f"SELECT ?o WHERE {{ tgc:{lesson} tgc:CoversTopic ?o }}")
    if topics:
        facts.append("Sujet : " + ", ".join(t["o"] for t in topics))
    pre = run_sparql(f"SELECT ?o WHERE {{ tgc:{lesson} tgc:hasPreLesson ?o }}")
    if pre:
        facts.append("Leçon préalable : " + ", ".join(p["o"] for p in pre))

    # Profil de l'enseignant (ce qu'il aime / son style)
    if teacher:
        pt = run_sparql(f"SELECT ?o WHERE {{ tgc:{teacher} tgc:hasPlayerType ?o }}")
        st = run_sparql(f"SELECT ?o WHERE {{ tgc:{teacher} tgc:has_TeachingStyle ?o }}")
        profil = []
        if pt:
            profil.append("player type = " + ", ".join(x["o"] for x in pt))
        if st:
            profil.append("style = " + ", ".join(x["o"] for x in st))
        if profil:
            facts.append(f"Profil de l'enseignant {teacher} : " + " ; ".join(profil))

    # Ressources de la leçon + leurs éléments de jeu (type + objectif)
    resources = run_sparql(f"SELECT ?res WHERE {{ tgc:{lesson} tco:reuseResource ?res }}")
    res_lines = []
    for r in resources:
        res = r["res"]
        titre = run_sparql(f"SELECT ?x WHERE {{ tgc:{res} tgc:has_title ?x }}")
        titre = titre[0]["x"] if titre else res
        elems = []
        for e in run_sparql(f"SELECT ?g WHERE {{ tgc:{res} tgc:containsGameElement ?g }}"):
            g = e["g"]
            types = run_sparql(f"SELECT ?t WHERE {{ tgc:{g} a ?t }}")
            type_ge = next((t["t"] for t in types if "Named" not in t["t"]), "?")
            objs = run_sparql(f"SELECT ?o WHERE {{ tgc:{g} tgc:relevantToObjective ?o }}")
            obj = ", ".join(o["o"] for o in objs) or "?"
            elems.append(f"{g} (type {type_ge}, objectif {obj})")
        ligne = f"- {titre}"
        if elems:
            ligne += " — éléments de jeu : " + " ; ".join(elems)
        res_lines.append(ligne)
    if res_lines:
        facts.append("Ressources de la leçon :\n" + "\n".join(res_lines))

    if not facts:
        return ""
    return "FAITS DE L'ONTOLOGIE (à utiliser tels quels, ne rien inventer) :\n" + "\n".join(facts)


def recommend(state):
    """Nœud Agent 2 : remplit sparql_query, query_results, recommendation, ontology_facts."""
    question = state.get("user_input", "")
    summary = state.get("ontology_summary") or "(aucun resume fourni)"
    context = _build_context(state)
    result = generate_and_run(question, summary, context=context)
    state["sparql_query"] = result["sparql_query"]
    state["query_results"] = result["query_results"]
    state["attempts"] = result["attempts"]
    state["recommendation"] = _format_recommendation(question, result["query_results"])
    state["ontology_facts"] = gather_ontology_facts(state)
    state["final_answer"] = state["recommendation"]
    return state


if __name__ == "__main__":
    # Petit test manuel : python -m src.agent.agent2
    summary = "tgc:designLesson : Teacher -> Lesson ; tco:reuseResource : Lesson -> Resource"
    res = generate_and_run(
        "Quelles ressources pour la lecon sur l'heritage ?",
        summary,
        context="- lecon : tgc:Lesson4_Inheritance",
    )
    print("SPARQL :\n", res["sparql_query"])
    print(_format_recommendation("", res["query_results"]))
