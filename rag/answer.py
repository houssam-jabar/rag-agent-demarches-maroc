import httpx
from retriever import rechercher_chunks

MODELE_LLM = "llama-3.3-70b-versatile"

PROMPT_SYSTEME = """Tu es un assistant qui repond aux questions sur l'etat civil au Maroc \
(acte de naissance, mariage, deces, livret de famille, etc.), en te basant UNIQUEMENT sur \
les extraits fournis ci-dessous.

Regles strictes :
- N'utilise que les informations presentes dans les extraits. N'invente rien.
- Si les extraits ne contiennent pas la reponse, dis clairement : \
"Je n'ai pas trouve cette information dans mes sources."
- Cite le titre de l'article source a la fin de ta reponse.
- Reponds en francais, de maniere claire et concise.
"""


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


def repondre(question, top_k=5):
    chunks = rechercher_chunks(question, top_k=top_k)
    contexte = construire_contexte(chunks)

    messages = [
        {"role": "system", "content": PROMPT_SYSTEME},
        {"role": "user", "content": f"Extraits disponibles :\n\n{contexte}\n\nQuestion : {question}"},
    ]

    api_key = _charger_cle_groq()
    r = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": MODELE_LLM, "messages": messages, "max_tokens": 500, "temperature": 0.2},
        timeout=30,
    )
    r.raise_for_status()
    reponse_texte = r.json()["choices"][0]["message"]["content"]

    sources = sorted(set((c["titre"], c["url"]) for c in chunks))
    return reponse_texte, sources


if __name__ == "__main__":
    question = "Quels documents faut-il pour declarer la naissance d'un enfant ?"
    reponse, sources = repondre(question)
    print("QUESTION:", question)
    print()
    print("REPONSE:", reponse)
    print()
    print("SOURCES:")
    for titre, url in sources:
        print(" -", titre, "|", url)
