import csv

with open("data/urls_etat_civil.csv", encoding="utf-8") as f:
    lecteur = csv.DictReader(f)
    lignes = list(lecteur)

print("Nombre de lignes trouvées :", len(lignes))
print("Premiere ligne :", lignes[0])