"""
Module de recherche semantique.
C'est CE fichier que l'Etudiant 4 importera.

Usage :
    from src.rag.retriever import retrieve
    resultats = retrieve("Comment motiver les eleves ?")
"""
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from sentence_transformers import CrossEncoder
import math
import os

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"  # cross-encoder multilingue
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
COLLECTION_NAME = "gamification_course"
DEFAULT_TOP_K = 3
FETCH_K = 20  # nb de candidats vectoriels recuperes avant re-ranking

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

# Re-ranker charge paresseusement (telechargement ~600 Mo a la 1re utilisation)
_reranker = None


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL, max_length=512, device="cpu")
    return _reranker


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _rerank(question: str, candidates, top_k: int):
    """
    Re-classe une liste de Documents par pertinence cross-encoder.
    Retourne les top_k Documents avec leur score [0, 1] (sigmoid des logits).
    """
    pairs = [[question, doc.page_content] for doc in candidates]
    logits = _get_reranker().predict(pairs, show_progress_bar=False)
    scored = sorted(
        zip(candidates, (float(s) for s in logits)),
        key=lambda x: x[1],
        reverse=True,
    )
    return [(doc, _sigmoid(score)) for doc, score in scored[:top_k]]


def retrieve(question: str, top_k: int = DEFAULT_TOP_K) -> list[str]:
    """
    Prend une question, retourne les top_k passages les plus pertinents.

    Pipeline en deux etapes :
      1. recherche vectorielle (FETCH_K candidats, recall maximal)
      2. re-ranking cross-encoder (precision maximale)

    Args:
        question: question de l'enseignant en langage naturel
        top_k: nombre de resultats (defaut: 3)

    Returns:
        liste de chaines (le texte de chaque chunk pertinent)
    """
    candidates = _vectorstore.similarity_search(question, k=FETCH_K)
    ranked = _rerank(question, candidates, top_k)
    return [doc.page_content for doc, _ in ranked]


def retrieve_with_scores(question: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Comme retrieve(), mais retourne aussi le score et la source de chaque chunk.

    Score : probabilite de pertinence du cross-encoder, dans [0, 1].
    1.0 = tres pertinent, 0.0 = non pertinent. Plus c'est haut, mieux c'est.
    """
    candidates = _vectorstore.similarity_search(question, k=FETCH_K)
    ranked = _rerank(question, candidates, top_k)
    return [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "Inconnue"),
            "score": round(score, 4),
        }
        for doc, score in ranked
    ]


# Test si execute directement
if __name__ == "__main__":
    import sys
    # Console Windows : forcer UTF-8 pour gerer accents, beta, etc.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
        print(f"\n{'-' * 60}\n")