import json
from pathlib import Path
import httpx
from sentence_transformers import SentenceTransformer

CHUNKS_FILE = Path("data/processed/chunks.jsonl")
INDEX_HOST = "pfa-etat-civil-fh6yu4i.svc.aped-4627-b74a.pinecone.io"
BATCH_SIZE = 50


def charger_cle_pinecone():
    with open(".env", encoding="utf-8") as f:
        for line in f:
            if line.startswith("PINECONE_API_KEY"):
                return line.strip().split("=", 1)[1]
    raise RuntimeError("PINECONE_API_KEY introuvable dans .env")


def main():
    api_key = charger_cle_pinecone()

    print("Chargement du modele d'embedding (1-2 min la premiere fois, telechargement)...")
    modele = SentenceTransformer("intfloat/multilingual-e5-base")

    with open(CHUNKS_FILE, encoding="utf-8") as f:
        chunks = [json.loads(l) for l in f]
    print(f"{len(chunks)} chunks a vectoriser")

    textes_prefixes = [f"passage: {c['texte']}" for c in chunks]
    embeddings = modele.encode(textes_prefixes, show_progress_bar=True, normalize_embeddings=True)

    vecteurs = []
    for chunk, embedding in zip(chunks, embeddings):
        vecteurs.append({
            "id": chunk["id"],
            "values": embedding.tolist(),
            "metadata": {
                "url": chunk["url"],
                "titre": chunk["titre"],
                "sous_categorie": chunk["sous_categorie"],
                "chunk_index": chunk["chunk_index"],
                "texte": chunk["texte"],
            },
        })

    print("Envoi vers Pinecone par lots...")
    with httpx.Client(timeout=30) as client:
        for i in range(0, len(vecteurs), BATCH_SIZE):
            lot = vecteurs[i:i + BATCH_SIZE]
            r = client.post(
                f"https://{INDEX_HOST}/vectors/upsert",
                headers={"Api-Key": api_key, "Content-Type": "application/json"},
                json={"vectors": lot},
            )
            r.raise_for_status()
            print(f"  lot {i}-{i + len(lot)} envoye")

    print("Termine.")


if __name__ == "__main__":
    main()
