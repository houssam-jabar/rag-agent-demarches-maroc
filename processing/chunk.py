import json
import hashlib
from pathlib import Path
import tiktoken

IN_FILE = Path("data/processed/documents_clean.jsonl")
OUT_FILE = Path("data/processed/chunks.jsonl")

TAILLE_CIBLE_TOKENS = 300
CHEVAUCHEMENT_TOKENS = 45  # environ 15% de 300

encodeur = tiktoken.get_encoding("cl100k_base")


def compter_tokens(texte):
    return len(encodeur.encode(texte))


def decouper_en_chunks(texte, titre, sous_categorie):
    tokens = encodeur.encode(texte)
    chunks = []
    debut = 0

    while debut < len(tokens):
        fin = min(debut + TAILLE_CIBLE_TOKENS, len(tokens))
        morceau_tokens = tokens[debut:fin]
        morceau_texte = encodeur.decode(morceau_tokens)

        contexte = f"État civil > {sous_categorie} > {titre}\n\n"
        chunks.append(contexte + morceau_texte)

        if fin == len(tokens):
            break
        debut = fin - CHEVAUCHEMENT_TOKENS

    return chunks


def main():
    with open(IN_FILE, encoding="utf-8") as f:
        documents = [json.loads(l) for l in f]

    tous_les_chunks = []
    for doc in documents:
        morceaux = decouper_en_chunks(doc["texte"], doc["titre"], doc["sous_categorie"])
        for i, morceau in enumerate(morceaux):
            chunk_id = hashlib.sha256(f"{doc['url']}#{i}".encode()).hexdigest()[:16]
            tous_les_chunks.append({
                "id": chunk_id,
                "url": doc["url"],
                "titre": doc["titre"],
                "sous_categorie": doc["sous_categorie"],
                "chunk_index": i,
                "texte": morceau,
                "nb_tokens": compter_tokens(morceau),
            })

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for chunk in tous_les_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"{len(documents)} documents -> {len(tous_les_chunks)} chunks -> {OUT_FILE}")
    moyenne = sum(c["nb_tokens"] for c in tous_les_chunks) / len(tous_les_chunks)
    print(f"Taille moyenne des chunks : {moyenne:.0f} tokens")


if __name__ == "__main__":
    main()
