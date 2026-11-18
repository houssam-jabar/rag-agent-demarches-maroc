import json
import re
from pathlib import Path

IN_FILE = Path("data/processed/documents.jsonl")
OUT_FILE = Path("data/processed/documents_clean.jsonl")

LIGNES_BRUIT_EXACTES = {
    "vous avez des questions sur",
    "vos",
    "démarches au maroc",
    "démarches au maroc ?",
    "?",
    "nos conseillers vous répondent",
    "nos conseillers sont là pour vous aider",
    "gagnez du temps et de la sérénité ! contactez-nous dès maintenant pour des réponses précises en quelques minutes.",
    "évitez les démarches compliquées : contactez-nous dès maintenant pour des réponses claires et rapides.",
    "090 488 623",
    "(2€/min)",
    "par",
}

MOTIFS_BRUIT_PARTIEL = [
    "mise à jour le",
]


def est_ligne_bruit(ligne):
    l = ligne.strip().lower()
    if not l:
        return True
    if l in LIGNES_BRUIT_EXACTES:
        return True
    if any(motif in l for motif in MOTIFS_BRUIT_PARTIEL):
        return True
    return False


def nettoyer_texte(texte):
    lignes = texte.split("\n")
    lignes_gardees = [l for l in lignes if not est_ligne_bruit(l)]
    return "\n".join(lignes_gardees)


def main():
    with open(IN_FILE, encoding="utf-8") as f:
        documents = [json.loads(l) for l in f]

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for doc in documents:
            texte_propre = nettoyer_texte(doc["texte"])
            doc_propre = {
                **doc,
                "texte": texte_propre,
                "longueur_texte": len(texte_propre),
            }
            f.write(json.dumps(doc_propre, ensure_ascii=False) + "\n")

    print(f"{len(documents)} documents nettoyes -> {OUT_FILE}")


if __name__ == "__main__":
    main()
