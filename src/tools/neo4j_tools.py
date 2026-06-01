"""Outils Neo4j pour interroger l'ontologie."""
from src.db.neo4j_client import ontology_graph


def get_ontology_schema() -> dict:
    """Retourne le schéma de l'ontologie pour que l'agent IA le comprenne.

    Returns:
        dict: {
            "node_labels": [...],
            "relationship_types": [...],
            "node_properties": {...}
        }
    """
    try:
        # Labels disponibles
        labels_query = "CALL db.labels() YIELD label RETURN label"
        labels = ontology_graph.run(labels_query)
        node_labels = [item["label"] for item in labels]

        # Types de relations
        rel_query = "MATCH ()-[r]->() RETURN DISTINCT type(r) as rel_type LIMIT 80"
        rels = ontology_graph.run(rel_query)
        relationship_types = [item["rel_type"] for item in rels]

        # Propriétés par label (sample)
        node_properties = {}
        for label in node_labels[:5]:  # Limiter pour perf
            props_query = f"MATCH (n:{label}) RETURN keys(n) as props LIMIT 3"
            result = ontology_graph.run(props_query)
            if result:
                node_properties[label] = result[0].get("props", [])

        return {
            "node_labels": node_labels,
            "relationship_types": relationship_types,
            "node_properties": node_properties,
            "example_query": "MATCH (n) WHERE n.rdfs__label CONTAINS 'Gamif' RETURN n LIMIT 5"
        }
    except Exception as e:
        return {"error": f"Impossible d'extraire le schéma: {str(e)}"}


def query_ontology(cypher_query: str, params: dict = None) -> list[dict]:
    """Envoie une requête Cypher à l'ontologie Neo4j.

    Args:
        cypher_query: Requête Cypher valide
        params: Paramètres optionnels (ex: {"name": "value"})

    Returns:
        list[dict]: Résultats structurés ou erreur

    Example:
        >>> query_ontology("MATCH (n) WHERE n.rdfs__label = $label RETURN n", {"label": "Gamification"})
    """
    if not cypher_query or not isinstance(cypher_query, str):
        return [{"error": "Requête invalide"}]

    try:
        results = ontology_graph.run(cypher_query, params or {})
        return results if results else [{"message": "Aucun résultat"}]
    except Exception as e:
        return [{"error": str(e)}]


def get_concept_details(concept_name: str) -> dict:
    """Récupère les détails complets d'un concept.

    Args:
        concept_name: Nom du concept (ex: "Gamification")

    Returns:
        dict: Concept avec définition, propriétés et relations
    """
    query = f"""
    MATCH (n)
    WHERE n.rdfs__label CONTAINS $name OR n.uri CONTAINS $name
    OPTIONAL MATCH (n)-[r]-(m)
    RETURN {{
        uri: n.uri,
        label: n.rdfs__label,
        comment: n.rdfs__comment,
        properties: apoc.map.filterValues(n, (k, v) => k STARTS WITH 'rdfs' OR k STARTS WITH 'rdf'),
        relations: collect(DISTINCT {{type: type(r), target: m.rdfs__label}})
    }} as concept
    LIMIT 1
    """
    try:
        results = ontology_graph.run(query, {"name": concept_name})
        return results[0] if results else {"error": f"Concept '{concept_name}' non trouvé"}
    except Exception as e:
        return {"error": str(e)}


########################################
#FONCTION DE SUPPORT POUR LE LLM : GENERER CONNAISSANCE MINIMALE DE L'ONTOLOGIE
########################################

#plus important 

#extraire les types de noeuds 


lister toutes les classes de l'ontologie 

MATCH (c:Class)
RETURN c.uri AS classURI
ORDER BY classURI;



#extraire les types de relations et le sens 

#extraire les labels et les noms exacts 





#secondaire 


#extraire la hiérarchie des classes 

#extaire le domaine et la portée des propriétés 

#extraire les uri 