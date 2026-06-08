"""
Recommandation de PERSONNES (enseignants) — pendant « humain » de l'Agent 2.

Au lieu de recommander une ressource gamifiée, ce module répond à des questions
du type « quel collègue plus expérimenté peut m'aider / me mentorer ? » ou
« quels profs ont un profil proche du mien ? ».

Tout est DÉTERMINISTE : on interroge directement les relations entre enseignants
DÉJÀ inférées dans l'ontologie (règles SWRL matérialisées via Protégé/Drools) :
  - tgc:potentialMentorOf  (mentor -> mentoré)
  - tgc:hasSimilarProfile  (même player type + même domaine/topic, symétrique)
  - tgc:hasSimilarDomain   (même spécialité, symétrique) — repli
Aucun LLM, donc aucune hallucination possible sur l'identité des personnes.
"""

from ..tools.sparql_tools import run_sparql


def _teacher_card(teacher: str) -> dict:
    """Récupère la « fiche » d'un enseignant (nom, spécialité, niveau, style…)."""
    def one(query, var):
        rows = run_sparql(query)
        return rows[0][var] if rows else None

    def many(query, var):
        return [r[var] for r in run_sparql(query) if r.get(var)]

    return {
        "id": teacher,
        "name": one(f"SELECT ?x WHERE {{ tgc:{teacher} tgc:has_Name ?x }}", "x") or teacher,
        "specialization": one(f"SELECT ?x WHERE {{ tgc:{teacher} tgc:specializedIn ?x }}", "x"),
        "teaching_style": one(f"SELECT ?x WHERE {{ tgc:{teacher} tgc:has_TeachingStyle ?x }}", "x"),
        "gamification_level": one(
            f"SELECT ?lvl WHERE {{ tgc:{teacher} tgc:hasGamificationExperience ?e . "
            f"?e tgc:experienceLevel ?lvl }}", "lvl"),
        "digital_competencies": many(
            f"SELECT ?x WHERE {{ tgc:{teacher} tgc:hasDigitalCompetency ?x }}", "x"),
        "lessons": many(f"SELECT ?x WHERE {{ tgc:{teacher} tgc:designLesson ?x }}", "x"),
    }


def gather_people(teacher: str) -> dict:
    """
    Recommande des personnes pour un enseignant donné, à partir des relations
    déjà présentes dans l'ontologie.

    Retour : {"mentors": [card...], "peers": [card...]}
      - mentors : enseignants proposés comme mentors potentiels (plus experts,
        même domaine, même espace de travail).
      - peers   : enseignants au profil similaire (échange entre pairs).
    """
    if not teacher:
        return {"mentors": [], "peers": []}

    mentors = [r["m"] for r in run_sparql(
        f"SELECT ?m WHERE {{ ?m tgc:potentialMentorOf tgc:{teacher} }}")]

    # Pairs : profil similaire (player type + domaine/topic) ; repli sur le domaine seul.
    peers = [r["p"] for r in run_sparql(
        f"SELECT ?p WHERE {{ tgc:{teacher} tgc:hasSimilarProfile ?p }}")]
    if not peers:
        peers = [r["p"] for r in run_sparql(
            f"SELECT ?p WHERE {{ tgc:{teacher} tgc:hasSimilarDomain ?p }}")]

    # On ne propose pas un mentor également listé comme simple pair (le mentorat prime).
    peers = [p for p in peers if p not in mentors]

    return {
        "mentors": [_teacher_card(m) for m in mentors],
        "peers": [_teacher_card(p) for p in peers],
    }


def _format_card(card: dict) -> str:
    """Une ligne lisible décrivant un enseignant recommandé + sa justification."""
    bits = []
    if card.get("specialization"):
        bits.append(f"spécialité {card['specialization']}")
    if card.get("gamification_level") is not None:
        bits.append(f"expérience gamification niveau {card['gamification_level']}")
    if card.get("teaching_style"):
        bits.append(f"style {card['teaching_style']}")
    if card.get("digital_competencies"):
        bits.append("compétences " + ", ".join(card["digital_competencies"]))
    ligne = f"- **{card['name']}**"
    if bits:
        ligne += " — " + " ; ".join(bits)
    if card.get("lessons"):
        ligne += "\n  Leçons conçues : " + ", ".join(card["lessons"][:3])
    return ligne


def format_people_reco(teacher: str, data: dict) -> str:
    """Texte final (Markdown) listant mentors et pairs recommandés."""
    mentors, peers = data["mentors"], data["peers"]
    if not mentors and not peers:
        return (f"Aucune personne à recommander pour {teacher} : l'ontologie ne "
                "contient ni mentor potentiel ni pair au profil similaire pour ce profil.")

    parts = [f"Recommandations de personnes pour **{teacher}** "
             "(d'après les relations inférées dans l'ontologie) :"]
    if mentors:
        parts.append("\n### Mentors potentiels (plus expérimentés, même domaine)\n"
                     + "\n".join(_format_card(c) for c in mentors))
    if peers:
        parts.append("\n### Pairs au profil similaire (pour échanger)\n"
                     + "\n".join(_format_card(c) for c in peers))
    return "\n".join(parts)


def recommend_people(state):
    """Nœud LangGraph : remplit people_recommendations, recommendation, final_answer."""
    teacher = state.get("teacher", "")
    data = gather_people(teacher)
    state["people_recommendations"] = data
    answer = format_people_reco(teacher, data)
    state["recommendation"] = answer
    state["final_answer"] = answer
    return state


if __name__ == "__main__":
    # Test manuel sans clé API : python -m src.agent.people [Teacher]
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "Sara"
    print(format_people_reco(t, gather_people(t)))
