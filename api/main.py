import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rag"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from answer import repondre_stream

app = FastAPI(
    title="Chatbot Etat Civil API",
    description="API RAG pour repondre aux questions sur l'etat civil marocain.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageItem(BaseModel):
    role: str = Field(..., description="'user' ou 'bot'")
    texte: str = Field(..., min_length=1)


class QuestionRequest(BaseModel):
    messages: list[MessageItem] = Field(..., min_length=1, description="Historique complet de la conversation")
    top_k: int = Field(5, ge=1, le=10, description="Nombre de chunks a recuperer")


@app.get("/")
def racine():
    return {"message": "API du chatbot Etat Civil. Voir /docs pour la documentation interactive."}


@app.get("/health")
def sante():
    return {"status": "ok"}


@app.post("/chat")
def chat(payload: QuestionRequest):
    historique = [{"role": m.role, "texte": m.texte} for m in payload.messages]

    def flux():
        try:
            for morceau in repondre_stream(historique, top_k=payload.top_k):
                yield morceau
        except Exception as e:
            yield f"\nUne erreur est survenue : {e}"

    return StreamingResponse(flux(), media_type="text/plain; charset=utf-8")
