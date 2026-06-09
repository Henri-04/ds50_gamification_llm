"""
src/reason.py — Régénère l'ontologie inférée (ontologies/TGC_inferred.owl).

Lance UNIQUEMENT le raisonneur Pellet sur l'ontologie de travail et matérialise
les relations SWRL entre enseignants (potentialMentorOf, hasSimilarProfile,
hasSimilarDomain, moreExpertThan…), utilisées par la recommandation de personnes.

À relancer après chaque modification de l'ontologie de travail.

⚠ Nécessite Java 25+ : les jars Pellet embarqués par owlready2 >= 0.50 sont
compilés pour Java 25 (sinon : UnsupportedClassVersionError).

Lancement (depuis la racine du projet) :
    python -m src.reason
"""

from .agent.agent1 import run_reasoner


def main() -> None:
    run_reasoner()


if __name__ == "__main__":
    main()
