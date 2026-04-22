"""
Decoupage des documents en chunks de taille fixe avec overlap.
Filtre les chunks trop courts (titres, en-tetes) qui polluent les resultats.
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 500      # caracteres par chunk (maximum)
CHUNK_OVERLAP = 50    # chevauchement entre chunks consecutifs
MIN_CHUNK_SIZE = 80   # taille minimum pour garder un chunk


def chunk_documents(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """
    Decoupe une liste de Documents en chunks plus petits.
    Filtre les chunks de moins de MIN_CHUNK_SIZE caracteres
    (titres seuls, en-tetes, lignes vides) qui n'apportent rien a la recherche.

    Args:
        documents: liste de Documents LangChain (sortie du loader)
        chunk_size: taille max d'un chunk en caracteres
        chunk_overlap: chevauchement entre chunks

    Returns:
        liste de Documents LangChain (les chunks)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    raw_chunks = splitter.split_documents(documents)

    # Filtrer les chunks trop courts (titres, en-tetes isolees)
    chunks = [c for c in raw_chunks if len(c.page_content.strip()) >= MIN_CHUNK_SIZE]

    filtered = len(raw_chunks) - len(chunks)
    if filtered > 0:
        print(f"  ({filtered} micro-chunks filtres, < {MIN_CHUNK_SIZE} chars)")

    return chunks


# Test si execute directement
if __name__ == "__main__":
    from loader import load_documents

    print("=== Test du chunker ===")
    docs = load_documents()
    chunks = chunk_documents(docs)

    print(f"\nDocuments charges : {len(docs)}")
    print(f"Chunks crees : {len(chunks)}")

    sizes = [len(c.page_content) for c in chunks]
    print(f"Taille moyenne : {sum(sizes) // len(sizes)} caracteres")
    print(f"Min : {min(sizes)} | Max : {max(sizes)}")

    print(f"\n--- Exemple (chunk 5) ---")
    print(chunks[4].page_content)