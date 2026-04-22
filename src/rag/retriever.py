"""
Module de recherche semantique.
C'est CE fichier que l'Etudiant 4 importera.

Usage :
    from src.rag.retriever import retrieve
    resultats = retrieve("Comment motiver les eleves ?")
"""
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
COLLECTION_NAME = "gamification_course"
DEFAULT_TOP_K = 3

# Chargement (une seule fois a l'import du module)
_embedding_fn = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)
_vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=_embedding_fn,
    collection_name=COLLECTION_NAME
)


def retrieve(question: str, top_k: int = DEFAULT_TOP_K) -> list[str]:
    """
    Prend une question, retourne les top_k passages les plus pertinents.

    Args:
        question: question de l'enseignant en langage naturel
        top_k: nombre de resultats (defaut: 3)

    Returns:
        liste de chaines (le texte de chaque chunk pertinent)
    """
    docs = _vectorstore.similarity_search(question, k=top_k)
    return [doc.page_content for doc in docs]


def retrieve_with_scores(question: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Comme retrieve(), mais retourne aussi les scores et sources.
    """
    results = _vectorstore.similarity_search_with_score(question, k=top_k)
    return [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "Inconnue"),
            "score": round(score, 4)
        }
        for doc, score in results
    ]


# Test si execute directement
if __name__ == "__main__":
    questions = [
        "Comment encoder des valeurs ?",
        "Quels sont les elements de jeu utilises en gamification ?",
        "Quels sont les risques de la gamification ?",
    ]

    print("=== Test du retriever ===\n")
    for q in questions:
        print(f"Q: {q}")
        results = retrieve_with_scores(q, top_k=3)
        for i, r in enumerate(results, 1):
            source = os.path.basename(r["source"])
            print(f"\n  {i}. [score: {r['score']}] (source: {source})")
            print(f"     {r['content'][:200]}")
        print(f"\n{'─' * 60}\n")