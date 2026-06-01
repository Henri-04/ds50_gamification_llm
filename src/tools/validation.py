"""Validation stricte des recommandations contre l'ontologie."""
import re
from typing import Tuple


def validate_against_ontology(
    recommendation: str,
    ontology_rules: list[dict],
) -> Tuple[bool, list[str]]:
    """Valide que la recommandation respecte 100% les règles de l'ontologie."""
    errors = []

    if not ontology_rules:
        errors.append("Aucune règle d'ontologie disponible pour valider.")
        return False, errors

    # Extraire concepts valides
    valid_concepts = _extract_valid_concepts(ontology_rules)
    proposed_concepts = _extract_concepts_from_text(recommendation)

    # Vérifier que chaque concept existe
    for concept in proposed_concepts:
        if concept.lower() not in [c.lower() for c in valid_concepts]:
            errors.append(f"Concept '{concept}' n'existe pas dans l'ontologie.")

    is_valid = len(errors) == 0
    return is_valid, errors


def _extract_valid_concepts(ontology_rules: list[dict]) -> list[str]:
    """Extraire liste des concepts valides de l'ontologie."""
    concepts = []
    for rule in ontology_rules:
        if "concept" in rule:
            concepts.append(rule["concept"])
    return list(set(concepts))


def _extract_concepts_from_text(text: str) -> list[str]:
    """Extraire concepts mentionnés dans le texte."""
    patterns = [
        r"(?:concept|élément|mécanisme|stratégie)\s+(?:de\s+)?([A-Z][a-z]+)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    ]

    concepts = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        concepts.extend(matches)

    return list(set(concepts))
