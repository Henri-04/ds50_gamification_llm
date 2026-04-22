"""
Chargement des documents depuis le dossier data/.
Parcourt RECURSIVEMENT les sous-dossiers (data/coursera_gamification/, data/cours_DS52/, etc.)
Supporte les fichiers .txt et .pdf.
"""
from langchain_community.document_loaders import TextLoader, PyPDFLoader
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def load_documents(data_dir=DATA_DIR):
    """
    Charge tous les fichiers .txt et .pdf du dossier data/ et ses sous-dossiers.
    Retourne une liste de Documents LangChain.
    """
    documents = []

    for root, dirs, files in os.walk(data_dir):
        for filename in sorted(files):
            filepath = os.path.join(root, filename)
            # Chemin relatif pour un affichage lisible
            rel_path = os.path.relpath(filepath, data_dir)

            if filename.endswith(".txt"):
                loader = TextLoader(filepath, encoding="utf-8")
                docs = loader.load()
                documents.extend(docs)
                print(f"  [TXT] {rel_path} : {len(docs)} document(s)")

            elif filename.endswith(".pdf"):
                loader = PyPDFLoader(filepath)
                docs = loader.load()
                documents.extend(docs)
                print(f"  [PDF] {rel_path} : {len(docs)} page(s)")

    return documents


# Test si execute directement
if __name__ == "__main__":
    print("=== Test du loader ===")
    docs = load_documents()
    print(f"\nTotal : {len(docs)} document(s) charge(s)")
    if docs:
        print(f"Premier document (extrait) : {docs[0].page_content[:200]}...")