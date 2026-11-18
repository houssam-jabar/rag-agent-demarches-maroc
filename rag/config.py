import os


def charger_variable_env(nom):
    valeur = os.environ.get(nom)
    if valeur:
        return valeur

    if os.path.exists(".env"):
        with open(".env", encoding="utf-8") as f:
            for line in f:
                if line.startswith(nom + "="):
                    return line.strip().split("=", 1)[1]

    raise RuntimeError(f"{nom} introuvable (ni variable d'environnement, ni .env)")
