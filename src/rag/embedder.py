"""
Transformation des chunks en vecteurs et stockage dans ChromaDB.
"""
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os
import shutil

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
COLLECTION_NAME = "gamification_course"


def get_embedding_function():
    """Retourne le modele d'embedding configure."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )


def embed_and_store(chunks, reset=True):
    """
    Vectorise les chunks et les stocke dans ChromaDB.

    Args:
        chunks: liste de Documents LangChain (sortie du chunker)
        reset: si True, supprime l'ancienne base avant d'inserer

    Returns:
        l'objet vectorstore Chroma
    """
    if reset and os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
        print(f"  Ancienne base supprimee")

    print(f"  Chargement du modele {EMBEDDING_MODEL}...")
    embedding_fn = get_embedding_function()

    # Test rapide
    test_vec = embedding_fn.embed_query("test")
    print(f"  Dimension des vecteurs : {len(test_vec)}")

    print(f"  Vectorisation et stockage de {len(chunks)} chunks...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_fn,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
        collection_metadata={"hnsw:space": "cosine"}
    )

    count = vectorstore._collection.count()
    print(f"  {count} vecteurs stockes dans {CHROMA_DIR}")
    return vectorstore


# Test si execute directement
if __name__ == "__main__":
    from loader import load_documents
    from chunker import chunk_documents

    print("=== Test de l'embedder ===\n")

    print("[1] Chargement...")
    docs = load_documents()

    print("\n[2] Chunking...")
    chunks = chunk_documents(docs)

    print(f"\n[3] Embedding + stockage...")
    vectorstore = embed_and_store(chunks)

    print("\n=== Termine ===")