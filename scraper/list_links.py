import httpx
from bs4 import BeautifulSoup

url = "https://www.demarchesmaroc.com/etat-civil/"
response = httpx.get(url, timeout=20)
print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

tous_les_liens = soup.find_all("a")
print("Nombre total de liens <a> sur la page :", len(tous_les_liens))

liens_lire_suite = [a for a in tous_les_liens if "lire la suite" in a.get_text().lower()]
print("Nombre de liens 'lire la suite' trouves :", len(liens_lire_suite))

urls_trouvees = set()
for lien in liens_lire_suite:
    href = lien.get("href")
    if href:
        urls_trouvees.add(href)

for u in sorted(urls_trouvees):
    print(u)

print("\n--- Apercu des 30 premiers liens de la page (diagnostic) ---")
for a in tous_les_liens[:30]:
    print(repr(a.get_text().strip()), "->", a.get("href"))