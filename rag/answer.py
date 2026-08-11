import json
import re
import httpx
from retriever import rechercher_chunks

MODELE_LLM = "llama-3.3-70b-versatile"

MARQUEUR_SOURCES = "<<<SOURCES>>>"

PROMPT_SYSTEME = """Tu es un conseiller qui aide les usagers avec les demarches d'etat civil au Maroc \
(acte de naissance, mariage, deces, livret de famille, etc.), en te basant UNIQUEMENT sur les extraits \
fournis ci-dessous.

Comportement attendu :
- Donne toujours la meilleure reponse possible avec les informations deja disponibles (question et \
historique), meme si elle est generale.
- Si un detail manquant changerait significativement la reponse (nee au Maroc ou a l'etranger, \
marocaine ou etrangere, majeure ou mineure, premiere demande ou duplicata...), ajoute UNE SEULE \
question de clarification courte a la toute fin de ta reponse.
- Ne repete jamais une clarification deja demandee dans l'historique : utilise la reponse de \
l'utilisateur pour affiner, sans reposer la meme question.
- Apres au maximum une clarification sur un meme sujet, donne une reponse finale, meme approximative.
- N'utilise que les informations presentes dans les extraits fournis. N'invente rien. Si les extraits \
ne contiennent pas la reponse, dis clairement que tu n'as pas trouve l'information.
- Structure toujours tes reponses en Markdown : mets en gras (**...**) la phrase qui introduit une \
liste (celle qui se termine par ":"), puis liste les elements avec des tirets "- " un par ligne. \
Utilise une liste numerotee "1. 2. 3." uniquement quand l'ordre des etapes compte reellement.
- Ne mentionne jamais le nom des sources, des articles, ni le numero d'un extrait (ex: "extrait 3") \
dans ta reponse : integre directement l'information, les sources sont affichees separement par l'interface.
- Reponds en francais, de maniere claire, concise et professionnelle.
"""

MOTIF_SOURCE_FINALE = re.compile(
    r"\n*\s*(source|sources)\s*:.*$", re.IGNORECASE | re.DOTALL
)


def _charger_cle_groq():
    with open(".env", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY"):
                return line.strip().split("=", 1)[1]
    raise RuntimeError("GROQ_API_KEY introuvable dans .env")


def construire_contexte(chunks):
    blocs = []
    for i, c in enumerate(chunks, start=1):
        blocs.append(f"[Extrait {i} - source: {c['titre']}]\n{c['texte']}")
    return "\n\n".join(blocs)


def _role_groq(role):
    return "assistant" if role == "bot" else "user"


def nettoyer_reponse(texte):
    texte = MOTIF_SOURCE_FINALE.sub("", texte)
    return texte.strip()


def _preparer_appel(historique, top_k):
    questions_utilisateur = [t["texte"] for t in historique if t["role"] == "user"]
    requete_recherche = " ".join(questions_utilisateur)
    chunks = rechercher_chunks(requete_recherche, top_k=top_k)
    contexte = construire_contexte(chunks)

    messages = [
        {"role": "system", "content": f"{PROMPT_SYSTEME}\n\nExtraits disponibles :\n\n{contexte}"}
    ]
    for tour in historique:
        messages.append({"role": _role_groq(tour["role"]), "content": tour["texte"]})

    sources = sorted(set((c["titre"], c["url"]) for c in chunks))
    return messages, sources


def repondre(historique, top_k=5):
    messages, sources = _preparer_appel(historique, top_k)

    api_key = _charger_cle_groq()
    r = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": MODELE_LLM, "messages": messages, "max_tokens": 500, "temperature": 0.2},
        timeout=30,
    )
    r.raise_for_status()
    reponse_texte = nettoyer_reponse(r.json()["choices"][0]["message"]["content"])

    return reponse_texte, sources


def repondre_stream(historique, top_k=5):
    messages, sources = _preparer_appel(historique, top_k)
    api_key = _charger_cle_groq()

    with httpx.stream(
        "POST",
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": MODELE_LLM, "messages": messages, "max_tokens": 500, "temperature": 0.2, "stream": True},
        timeout=30,
    ) as r:
        r.raise_for_status()
        for ligne in r.iter_lines():
            if not ligne or not ligne.startswith("data: "):
                continue
            charge = ligne[len("data: "):]
            if charge == "[DONE]":
                break
            morceau = json.loads(charge)
            delta = morceau["choices"][0]["delta"].get("content")
            if delta:
                yield delta

    donnees_sources = [{"titre": t, "url": u} for t, u in sources]
    yield f"\n{MARQUEUR_SOURCES}{json.dumps(donnees_sources, ensure_ascii=False)}"


if __name__ == "__main__":
    historique = [{"role": "user", "texte": "Comment obtenir un acte de naissance ?"}]
    for morceau in repondre_stream(historique):
        print(morceau, end="", flush=True)
