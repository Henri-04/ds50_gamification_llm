"""Prompts structurés pour chaque nœud du graphe."""

ANALYZE_QUERY_PROMPT = """
Tu es un expert en pédagogie et gamification. Analyse la question utilisateur.

Contexte de l'ontologie disponible:
{ontology_schema}

Historique de conversation:
{conversation_history}

Question utilisateur: {current_query}

Tâche:
1. Identifie les concepts clés de l'ontologie pertinents pour cette question
2. Liste les requêtes Cypher à exécuter pour récupérer les règles
3. Explique le raisonnement étape par étape

Réponds en JSON structuré:
{{
  "reasoning_steps": ["étape 1", "étape 2", ...],
  "required_cypher_queries": [
    "MATCH (n:Concept) WHERE n.name = '...' RETURN n",
    "MATCH (a:Concept)-[r:relationship]-(b:Concept) RETURN a, r, b",
    ...
  ],
  "concepts_to_explore": ["Motivation", "Feedback", ...]
}}
"""

FETCH_ONTOLOGY_PROMPT = """
Aucun prompt LLM - ce nœud exécute les requêtes Cypher directement.
Les résultats sont parsés et accumulés.
"""

FETCH_RAG_PROMPT = """
Aucun prompt LLM - ce nœud appelle retrieve_with_scores() directement.
Les passages sont formatés et accumulés.
"""

GENERATE_DRAFT_PROMPT = """
Tu es un expert en pédagogie et conception gamifiée. Génère une recommandation de gamification.

RÈGLES DE L'ONTOLOGIE (MUST FOLLOW - respecte strictement):
{ontology_rules}

CONTENU DES COURS PERTINENTS (pour enrichir):
{rag_content}

HISTORIQUE DE CONVERSATION:
{conversation_history}

QUESTION UTILISATEUR: {current_query}

INSTRUCTIONS:
1. Ta recommandation DOIT respecter 100% les règles de l'ontologie listées ci-dessus
2. Enrichis ta réponse avec les éléments du cours quand pertinent
3. Cite les concepts et règles utilisées
4. Fournis une structure claire:
   - Stratégie principale
   - Éléments de gamification proposés (avec justification)
   - Ressources du cours pertinentes
5. Sois concis mais détaillé

Génère la recommandation:
"""

VALIDATE_PROMPT = """
Pas de prompt LLM - validation par pattern matching et vérification d'existence.
Chaque concept proposé est vérifié contre les règles de l'ontologie.
"""

REFINE_PROMPT = """
Feedback de validation:

Les éléments suivants ne sont pas conformes aux règles de l'ontologie:
{validation_errors}

Concepts valides dans l'ontologie:
{valid_concepts}

Propose une version révisée de ta recommandation qui respecte STRICTEMENT les règles:
"""

FORMAT_WITH_CITATIONS_PROMPT = """
Pas de prompt LLM - formatage automatique avec citations.
Utilise les sources (ontologie + RAG) pour générer la réponse finale.
"""
