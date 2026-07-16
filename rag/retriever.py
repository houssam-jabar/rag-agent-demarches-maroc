import httpx
from sentence_transformers import SentenceTransformer

INDEX_HOST = "pfa-etat-civil-fh6yu4i.svc.aped-4627-b74a.pinecone.io"

_modele = None


def _charger_modele():
    global _modele
    if _modele is None:
        _modele = SentenceTransformer("intfloat/multilingual-e5-base")
    return _modele


def _charger_cle_pinecone():
    with open(".env", encoding="utf-8") as f:
        for line in f:
            if line.startswith("PINECONE_API_KEY"):
                return line.strip().split("=", 1)[1]
    raise RuntimeError("PINECONE_API_KEY introuvable dans .env")


def rechercher_chunks(question, top_k=5):
    modele = _charger_modele()
    vecteur_question = modele.encode([f"query: {question}"], normalize_embeddings=True)[0].tolist()

    api_key = _charger_cle_pinecone()
    r = httpx.post(
        f"https://{INDEX_HOST}/query",
        headers={"Api-Key": api_key, "Content-Type": "application/json"},
        json={"vector": vecteur_question, "topK": top_k, "includeMetadata": True},
        timeout=15,
    )
    r.raise_for_status()

    resultats = []
    for match in r.json()["matches"]:
        resultats.append({
            "score": match["score"],
            "titre": match["metadata"]["titre"],
            "url": match["metadata"]["url"],
            "texte": match["metadata"]["texte"],
        })
    return resultats


if __name__ == "__main__":
    question = "Quels documents faut-il pour declarer la naissance d'un enfant ?"
    for chunk in rechercher_chunks(question, top_k=3):
        print(f"[{chunk['score']:.3f}] {chunk['titre']}")
