"""Client Neo4j minimal."""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv(".env", override=True)


class Neo4jClient:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def run(self, query: str, params: dict = None) -> list[dict]:
        """Exécute une requête Cypher et retourne les résultats."""
        if params is None:
            params = {}

        with self.driver.session() as session:
            result = session.run(query, params)
            return [dict(record) for record in result]

    def close(self):
        """Ferme la connexion."""
        self.driver.close()

ontology_graph = Neo4jClient()

#test de la connexioj à la bdd et requêtage simple
if __name__ == "__main__" :
    
    ontology_graph = Neo4jClient()
    results = ontology_graph.run("MATCH (n) RETURN count(n) as total")
    print(results)
