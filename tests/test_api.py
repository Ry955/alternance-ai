import os

os.environ["LLM_PROVIDER"] = "mock"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

OFFRE = "Alternance ingenieur data, 12 mois, Paris. Python, SQL, cloud Azure, CI/CD." * 2
PROFIL = "Etudiant ING3 a CY TECH, Python, SQL, Docker, projets cloud et BI." * 2


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyse_retourne_le_format_attendu():
    r = client.post("/api/analyse", json={"offre": OFFRE, "profil": PROFIL})
    assert r.status_code == 200
    data = r.json()
    assert 0 <= data["score"] <= 100
    assert len(data["points_forts"]) >= 3
    assert data["competences_manquantes"]
    assert len(data["lettre"]) > 100


def test_entree_trop_courte_refusee():
    r = client.post("/api/analyse", json={"offre": "trop court", "profil": PROFIL})
    assert r.status_code == 422


def test_page_accueil():
    assert client.get("/").status_code == 200
