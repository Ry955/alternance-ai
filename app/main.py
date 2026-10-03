"""API de l'assistant de candidature en alternance."""
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import llm

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger("alternance-ai")

STATIC_DIR = Path(__file__).parent / "static"
VERSION = os.getenv("APP_VERSION", "dev")

app = FastAPI(title="Assistant alternance", version=VERSION)


class DemandeAnalyse(BaseModel):
    offre: str = Field(min_length=30, max_length=8000)
    profil: str = Field(min_length=30, max_length=8000)


@app.get("/health")
def health():
    """Sonde de disponibilite utilisee par Azure Container Apps."""
    return {"status": "ok", "version": VERSION, "provider": llm.provider_name()}


@app.post("/api/analyse")
def analyse(demande: DemandeAnalyse):
    try:
        resultat = llm.analyser(demande.offre, demande.profil)
    except llm.LLMError as exc:
        logger.error("echec LLM: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("erreur inattendue")
        raise HTTPException(status_code=502, detail="Le service IA n'a pas repondu") from exc

    logger.info("analyse effectuee score=%s", resultat.get("score"))
    return resultat


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
