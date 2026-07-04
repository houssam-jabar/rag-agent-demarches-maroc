import httpx

url = "https://www.demarchesmaroc.com/obtenir-acte-de-naissance/"
response = httpx.get(url)

print("Status code:", response.status_code)
print("Longueur du contenu:", len(response.text))
print(response.text[:500])
from bs4 import BeautifulSoup

soup = BeautifulSoup(response.text, "html.parser")
container = soup.find("div", attrs={"data-widget_type": "theme-post-content.default"})

texte = container.get_text(separator="\n", strip=True)
print(texte[:1000])