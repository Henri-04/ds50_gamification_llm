"""
Outils SPARQL pour l'Agent 2 (Agent de recommandation).

Charge l'ontologie TGC (.owl) UNE SEULE FOIS en memoire (singleton module)
et expose `run_sparql()` pour executer une requete SPARQL dessus via rdflib.

L'ontologie est interrogee en local, sans Neo4j ni serveur RDF externe.
"""

from pathlib import Path
from rdflib import Graph
from rdflib.plugins.sparql import prepareQuery

# --- Localisation de l'ontologie -------------------------------------------
# Ce fichier est dans src/tools/ ; l'ontologie est dans ontologies/ a la racine
# du projet (../../ontologies/ depuis ici).
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY_PATH = _PROJECT_ROOT / "ontologies" / "TGC3March2026.owl"
# Ontologie enrichie par le raisonneur (regles SWRL), generee par l'Agent 1.
INFERRED_PATH = _PROJECT_ROOT / "ontologies" / "TGC_inferred.owl"

# --- Prefixes de l'ontologie -----------------------------------------------
# Filet de securite : injectes en tete de chaque requete pour que le LLM
# puisse ecrire "tgc:Sara" sans redeclarer les PREFIX a chaque fois.
PREFIXES = """\
PREFIX tgc: <http://www.hds.utc.fr/tgc/tbox#>
PREFIX tco: <http://www.hds.utc.fr/tco/tbox#>
PREFIX mc2: <http://www.hds.utc.fr/mc2/tbox#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

# --- Chargement singleton ---------------------------------------------------
_graph: Graph | None = None


def get_graph() -> Graph:
    """Retourne le graphe RDF, en le chargeant a la premiere demande."""
    global _graph
    if _graph is None:
        # Si le raisonneur a tourne (Agent 1), on utilise l'ontologie enrichie.
        chemin = INFERRED_PATH if INFERRED_PATH.exists() else ONTOLOGY_PATH
        if not chemin.exists():
            raise FileNotFoundError(f"Ontologie introuvable : {chemin}")
        g = Graph()
        # L'OWL est au format RDF/XML.
        g.parse(str(chemin), format="xml")
        _graph = g
    return _graph


def _has_prefixes(query: str) -> bool:
    return "PREFIX" in query.upper()


def run_sparql(query: str) -> list[dict]:
    """
    Execute une requete SPARQL SELECT (ou ASK) sur l'ontologie.

    Les PREFIX sont injectes automatiquement si la requete n'en declare pas.

    Retour : liste de lignes, chaque ligne etant un dict {variable: valeur_str}.
             Les IRIs sont raccourcies (on ne garde que le nom local apres '#').

    Leve une exception si la requete est syntaxiquement invalide (utile pour
    le retry de l'Agent 2).
    """
    g = get_graph()
    full_query = query if _has_prefixes(query) else PREFIXES + "\n" + query

    # prepareQuery valide la syntaxe et leve une exception explicite si KO.
    prepared = prepareQuery(full_query)
    results = g.query(prepared)

    rows: list[dict] = []
    for row in results:
        record = {}
        for var in results.vars:
            value = row[var]
            record[str(var)] = _shorten(value) if value is not None else None
        rows.append(record)
    return rows


def _shorten(value) -> str:
    """IRI -> nom local lisible ; litteral -> sa valeur."""
    text = str(value)
    if "#" in text:
        return text.rsplit("#", 1)[-1]
    if "/" in text and text.startswith("http"):
        return text.rsplit("/", 1)[-1]
    return text


if __name__ == "__main__":
    # Test rapide, sans LLM ni cle API : prouve que l'ontologie se charge
    # et qu'une requete figee renvoie de vraies donnees.
    print(f"Chargement de : {ONTOLOGY_PATH}")
    g = get_graph()
    print(f"Triplets charges : {len(g)}")

    demo = """
    SELECT ?res ?title WHERE {
      tgc:Sara tgc:designLesson ?lesson .
      ?lesson tco:reuseResource ?res .
      OPTIONAL { ?res tgc:has_title ?title }
    }
    """
    print("\nRessources des lecons concues par Sara :")
    for r in run_sparql(demo):
        print(" -", r)
