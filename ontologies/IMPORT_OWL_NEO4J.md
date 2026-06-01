# Import de l'ontologie TGC3March2026.owl dans Neo4j

## Objectif

Ce guide explique comment importer l'ontologie `TGC3March2026.owl` (format OWL/RDF-XML) dans Neo4j avec le plugin neosemantics (`n10s`).

But final: obtenir un graphe exploitable avec Cypher, puis l'utiliser dans un pipeline de type GraphRAG.

## Vue d'ensemble

Chaîne de traitement:

`OWL (RDF/XML) -> triplets RDF -> graphe Neo4j -> requêtes / RAG`

## Contexte de l'ontologie

L'ontologie modélise un contexte pédagogique gamifié: profil enseignant, objectifs pédagogiques, caractéristiques des apprenants, ressources pédagogiques et éléments de gamification.

Elle sert de base de connaissances pour des recommandations pédagogiques contextualisées.


## Prérequis

- Neo4j Desktop (ou Neo4j Server) installé
- Une base Neo4j créée et démarrée
- Fichier d'ontologie `TGC3March2026.owl` disponible


## Étapes d'import
### 1) Plugin
Ajouter le plugin neosemantics à la base Neo4j.
- Installer le plugin `neosemantics (n10s)` disponible ici: https://github.com/neo4j-labs/neosemantics/releases (télécharger le fichier `.jar`).

Ce plugin permet d'importer des données RDF/OWL et de transformer les triplets en graphe Neo4j.

- Dans Neo4j Desktop (`DB -> Open -> Instance folder -> plugins`), glisser-déposer le fichier `.jar` du plugin.

### 2) Activer les procédures n10s

Dans la configuration Neo4j (`DB -> ... -> Open -> neo4j.conf`), ajouter à la fin du fichier:

```properties
dbms.security.procedures.unrestricted=n10s.*
dbms.security.procedures.allowlist=n10s.*
```

Sauvegarder le fichier et redémarrer ensuite la base.

### 3) Initialiser la configuration RDF

Dans Neo4j Browser, exécuter:

```cypher
CALL n10s.graphconfig.init();
```

### 4) Créer la contrainte d'unicité

```cypher
CREATE CONSTRAINT n10s_unique_uri
FOR (r:Resource)
REQUIRE r.uri IS UNIQUE;
```

Cette contrainte évite les doublons sur les ressources RDF.


### 5) Importer l'ontologie

Copier `TGC3March2026.owl` dans le dossier `import` de la base Neo4j.
Puis lancer l'import avec URI raccourcies (plus lisible dans Neo4j):

```cypher
CALL n10s.rdf.import.fetch(
  "/Users/henribost/Library/Application Support/neo4j-desktop/Application/Data/dbmss/dbms-89ef1bd0-96e3-4be3-ba9f-675ae6d699a2/import/TGC3March2026.owl", 
  "RDF/XML",
  { handleVocabUris: "SHORTEN" }
);
```
Remplacer le chemin par votre chemin local.

Résultat attendu :  `1859` triplets importés.

## Vérification rapide

Après import, vérifier que des nœuds et relations ont été créés:

```cypher
MATCH (n) RETURN count(n) AS totalNodes;
```

```cypher
MATCH ()-[r]->() RETURN count(r) AS totalRelations;
```


