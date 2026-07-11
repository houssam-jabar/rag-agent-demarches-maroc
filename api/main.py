import sys
from pathlib import Path

# rag/answer.py utilise des imports simples (from retriever import ...), qui ne
# fonctionnent que si le dossier rag/ est sur le chemin de recherche Python.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rag"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from answer import repondre

app = FastAPI(
    title="Chatbot Etat Civil API",
    description="API RAG pour repondre aux questions sur l'etat civil marocain.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # a restreindre au domaine du frontend une fois deploye
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, description="La question de l'utilisateur")
    top_k: int = Field(5, ge=1, le=10, description="Nombre de chunks a recuperer")


class SourceItem(BaseModel):
    titre: str
    url: str


class ReponseModel(BaseModel):
    reponse: str
    sources: list[SourceItem]


@app.get("/")
def racine():
    return {"message": "API du chatbot Etat Civil. Voir /docs pour la documentation interactive."}


@app.get("/health")
def sante():
    return {"status": "ok"}


@app.post("/chat", response_model=ReponseModel)
def chat(payload: QuestionRequest):
    try:
        reponse_texte, sources = repondre(payload.question, top_k=payload.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la generation de la reponse : {e}")

    return {
        "reponse": reponse_texte,
        "sources": [{"titre": t, "url": u} for t, u in sources],
    }
