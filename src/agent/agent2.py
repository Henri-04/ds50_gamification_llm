"""
Agent 2 - Agent de recommandation.

Role : a chaque question de l'enseignant (langage naturel), traduire la
question en requete SPARQL ciblee, l'executer sur l'ontologie, et renvoyer
les donnees reelles (= "voici la ressource recommandee").

Chaine : question NL  --NLP (LLM)-->  SPARQL  --execute (rdflib)-->  donnees

Le LLM recoit :
  1. les PREFIX disponibles (pour ecrire du SPARQL executable),
  2. le resume de l'ontologie produit par l'Agent 1 (blob opaque : on
     n'en suppose aucune structure, c'est le LLM qui l'interprete),
  3. la question de l'enseignant.

Une boucle de retry bornee (le "while" du tableau) corrige la requete si
elle est invalide ou ne renvoie aucun resultat.
"""

import re
import sys
from pathlib import Path

# Permet de lancer ce fichier directement (python src/agent/agent2.py)
# en ajoutant src/ au chemin de recherche des modules.
_SRC = Path(__file__).resolve().parents[1]  # .../src
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from llm.groq_client import call_llm
from tools.sparql_tools import run_sparql, PREFIXES

try:
    from .state import AgentState
except ImportError:  # execution directe (python src/agent/agent2.py)
    AgentState = dict  # type: ignore

# Nombre maximum de tentatives de generation/execution de la requete.
MAX_RETRIES = 3


# --------------------------------------------------------------------------- #
# Construction du prompt
# --------------------------------------------------------------------------- #
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
- Privilegie un SELECT avec les variables utiles (titre, description, type...).
- Utilise OPTIONAL pour les proprietes qui peuvent manquer (ex. has_description).
"""


def _build_messages(question: str, summary: str, feedback: str | None) -> list[dict]:
    user_content = (
        f"Resume de l'ontologie (fourni par l'Agent 1) :\n{summary}\n\n"
        f"Question de l'enseignant :\n{question}"
    )
    if feedback:
        user_content += f"\n\nLa tentative precedente a echoue : {feedback}\n" \
                        "Corrige la requete SPARQL en consequence."
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


# --------------------------------------------------------------------------- #
# Extraction de la requete depuis la reponse du LLM
# --------------------------------------------------------------------------- #
def _extract_sparql(text: str) -> str:
    """Retire les balises markdown et le bavardage eventuel autour de la requete."""
    # Bloc ```sparql ... ``` ou ``` ... ```
    fenced = re.search(r"```(?:sparql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    # Sinon, on part du premier mot-cle SPARQL.
    match = re.search(r"(PREFIX|SELECT|ASK|CONSTRUCT)\b", text, re.IGNORECASE)
    if match:
        return text[match.start():].strip()
    return text.strip()


# --------------------------------------------------------------------------- #
# Mise en forme de la recommandation
# --------------------------------------------------------------------------- #
def _format_recommendation(question: str, rows: list[dict]) -> str:
    if not rows:
        return (
            "Aucune donnee correspondante n'a ete trouvee dans l'ontologie pour "
            "cette demande. Le sujet ne fait peut-etre pas partie du perimetre du "
            "cours."
        )
    lines = [f"{len(rows)} resultat(s) trouve(s) dans l'ontologie :"]
    for row in rows:
        parts = [f"{k}={v}" for k, v in row.items() if v is not None]
        lines.append("  - " + ", ".join(parts))
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Coeur reutilisable : NLP -> SPARQL -> execute -> retry
# --------------------------------------------------------------------------- #
def generate_and_run(question: str, summary: str, max_retries: int = MAX_RETRIES) -> dict:
    """
    Genere une requete SPARQL a partir de la question + du resume, l'execute,
    et reessaie (corrige) si elle est invalide ou renvoie 0 resultat.

    Retour : dict {sparql_query, query_results, attempts, error}.
    """
    feedback: str | None = None
    last_query = ""
    last_rows: list[dict] = []

    for attempt in range(1, max_retries + 1):
        response = call_llm(_build_messages(question, summary, feedback))
        last_query = _extract_sparql(response.choices[0].message.content)

        try:
            last_rows = run_sparql(last_query)
        except Exception as exc:  # requete invalide -> on renvoie l'erreur au LLM
            feedback = f"erreur de syntaxe SPARQL : {exc}"
            continue

        if last_rows:  # succes : on a des donnees reelles
            return {
                "sparql_query": last_query,
                "query_results": last_rows,
                "attempts": attempt,
                "error": None,
            }

        # Requete valide mais vide -> on demande une reformulation.
        feedback = "la requete etait valide mais n'a renvoye aucun resultat."

    # Echec apres toutes les tentatives.
    return {
        "sparql_query": last_query,
        "query_results": last_rows,
        "attempts": max_retries,
        "error": feedback,
    }


# --------------------------------------------------------------------------- #
# Noeud LangGraph
# --------------------------------------------------------------------------- #
def recommend(state: AgentState) -> AgentState:
    """Noeud Agent 2 : remplit sparql_query, query_results, recommendation."""
    question = state.get("user_input", "")
    summary = state.get("ontology_summary") or "(aucun resume fourni)"

    result = generate_and_run(question, summary)

    state["sparql_query"] = result["sparql_query"]
    state["query_results"] = result["query_results"]
    state["attempts"] = result["attempts"]
    state["recommendation"] = _format_recommendation(question, result["query_results"])
    state["final_answer"] = state["recommendation"]
    return state


# --------------------------------------------------------------------------- #
# Test autonome
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    from tools.sparql_tools import get_graph

    # Resume bouchon (a la place de l'Agent 1). Contient les noms exacts,
    # comme convenu : le LLM s'en sert pour ecrire le SPARQL.
    MOCK_SUMMARY = """\
Enseignante : tgc:Sara (profil tgc:hasPlayerType tgc:Socializer).

Chemins utiles dans le graphe (noms exacts) :
- Une lecon couvre un sujet : ?lesson tgc:CoversTopic ?topic .
  Ex. tgc:Lesson4_Inheritance tgc:CoversTopic tgc:InheritanceTopic .
- Une lecon reutilise ses ressources : ?lesson tco:reuseResource ?res .
- Une ressource gamifiee est de type tgc:GamifiedResource ; elle a un titre
  (tgc:has_title) et parfois une description (tgc:has_description).

Donc pour trouver les ressources gamifiees liees a un sujet : prendre la lecon
qui tgc:CoversTopic ce sujet, puis ses tco:reuseResource de type
tgc:GamifiedResource.
"""

    print(f"Triplets charges : {len(get_graph())}\n")

    questions = [
        "Quelles ressources gamifiees existent pour la lecon sur l'heritage ?",
        "Quel est le profil de joueur de Sara ?",
    ]

    for q in questions:
        print("=" * 70)
        print("Question :", q)
        try:
            res = generate_and_run(q, MOCK_SUMMARY)
            print("\nSPARQL genere :\n", res["sparql_query"])
            print(f"\nTentatives : {res['attempts']} | Erreur : {res['error']}")
            print("\n" + _format_recommendation(q, res["query_results"]))
        except Exception as exc:
            # Typiquement : pas de cle GROQ_API_KEY -> on retombe sur une
            # requete figee pour prouver que l'execution SPARQL fonctionne.
            print(f"\n[LLM indisponible : {exc}]")
            print("Fallback (requete figee) :")
            demo = """
            SELECT ?res ?title WHERE {
              tgc:Sara tgc:designLesson ?lesson .
              ?lesson tco:reuseResource ?res .
              OPTIONAL { ?res tgc:has_title ?title }
            }"""
            print(_format_recommendation(q, run_sparql(demo)))
        print()
