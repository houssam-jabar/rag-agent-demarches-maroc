import csv
import time
import json
import httpx
from pathlib import Path
from bs4 import BeautifulSoup

CSV_PATH = "data/urls_etat_civil.csv"
OUT_FILE = Path("data/processed/documents.jsonl")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

MAX_TENTATIVES = 4
ATTENTE_ENTRE_TENTATIVES = 8  # secondes ; le site est instable par intermittence


def trouver_container(soup):
    container = soup.find("div", attrs={"data-widget_type": "theme-post-content.default"})
    if container is not None:
        return container
    return soup.find("div", class_="elementor-widget-theme-post-content")


def extraire_article(url):
    response = httpx.get(url, timeout=20, follow_redirects=True)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    container = trouver_container(soup)
    if container is None:
        return None

    h1 = soup.find("h1")
    titre_reel = h1.get_text(strip=True) if h1 else None
    texte = container.get_text(separator="\n", strip=True)
    return titre_reel, texte


def main():
    with open(CSV_PATH, encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))

    resultats = []
    echecs = []

    for ligne in lignes:
        url = ligne["url"].strip()
        print(f"[fetch] {url}")

        extraction = None
        for tentative in range(1, MAX_TENTATIVES + 1):
            try:
                extraction = extraire_article(url)
                if extraction is not None:
                    if tentative > 1:
                        print(f"  -> reussi a la tentative {tentative}")
                    break
                print(f"  -> tentative {tentative}/{MAX_TENTATIVES} : conteneur introuvable (page vide cote site)")
            except Exception as e:
                print(f"  -> tentative {tentative}/{MAX_TENTATIVES} : erreur {e}")

            if tentative < MAX_TENTATIVES:
                time.sleep(ATTENTE_ENTRE_TENTATIVES)

        if extraction is None:
            print(f"  -> ECHEC DEFINITIF apres {MAX_TENTATIVES} tentatives : {url}")
            echecs.append(url)
        else:
            titre_reel, texte = extraction
            resultats.append({
                "url": url,
                "titre": titre_reel or ligne["titre"],
                "sous_categorie": ligne["sous_categorie"],
                "longueur_texte": len(texte),
                "texte": texte,
            })

        time.sleep(2)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for item in resultats:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nTermine : {len(resultats)} articles sauvegardes dans {OUT_FILE}")
    if echecs:
        print(f"Echecs ({len(echecs)}):")
        for u in echecs:
            print(" -", u)


if __name__ == "__main__":
    main()
