import httpx
import xml.etree.ElementTree as ET

MOTS_CLES = [
    "naissance", "mariage", "deces", "divorce", "civil", "casier",
    "fiancailles", "remariage", "islam", "famille", "livret",
    "concordance", "noms", "adoul", "kafala", "filiation", "adoption",
    "jugement", "rectification", "transcription",
]


def get_locs(url):
    response = httpx.get(url, timeout=20)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    return [el.text.strip() for el in root.iter() if el.tag.endswith("loc")]


def main():
    sitemap_principal = "https://www.demarchesmaroc.com/sitemap.xml"
    sous_sitemaps = get_locs(sitemap_principal)
    print(f"Sous-sitemaps trouves : {len(sous_sitemaps)}")
    for s in sous_sitemaps:
        print(" -", s)

    toutes_urls = []
    for sm in sous_sitemaps:
        if sm.endswith(".xml"):
            try:
                urls = get_locs(sm)
                toutes_urls.extend(urls)
                print(f"{sm} -> {len(urls)} urls")
            except Exception as e:
                print(f"erreur sur {sm}: {e}")

    print(f"\nTotal URLs sur tout le site : {len(toutes_urls)}")

    candidats = sorted(set(
        u for u in toutes_urls if any(mot in u.lower() for mot in MOTS_CLES)
    ))

    print(f"\nURLs potentiellement liees a l'etat civil : {len(candidats)}")
    for u in candidats:
        print(u)


if __name__ == "__main__":
    main()
