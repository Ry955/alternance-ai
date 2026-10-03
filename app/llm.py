"""Client LLM : Azure OpenAI, API compatible OpenAI, ou mock hors ligne."""
import json
import os

from openai import AzureOpenAI, OpenAI

SYSTEM_PROMPT = """Tu es un conseiller en recrutement spécialisé dans l'alternance en France.
On te donne une offre de stage ou d'alternance et le profil d'un candidat.
Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, au format :
{
  "score": <entier 0-100, compatibilité du profil avec l'offre>,
  "points_forts": [<3 à 5 chaînes : atouts du candidat pour cette offre>],
  "competences_manquantes": [<2 à 4 chaînes : ce qui manque, avec une piste concrète pour y remédier>],
  "lettre": "<lettre de motivation de 150 à 200 mots, ton professionnel, en français>"
}
Appuie-toi uniquement sur les éléments présents dans le profil : n'invente aucune expérience."""

MOCK_RESPONSE = {
    "score": 72,
    "points_forts": [
        "Formation d'ingénieur en informatique alignée sur le poste",
        "Projets cloud concrets : conteneurisation et CI/CD",
        "Pratique de Python et des bases de données",
    ],
    "competences_manquantes": [
        "Kubernetes en production : suivre le module AKS et déployer un cluster de test",
        "Terraform : refaire l'infrastructure du projet en infrastructure-as-code",
    ],
    "lettre": (
        "Madame, Monsieur,\n\nActuellement en troisième année du cycle ingénieur à CY TECH, "
        "je souhaite rejoindre votre équipe en alternance. Mon parcours m'a conduit à concevoir "
        "et déployer des applications conteneurisées, de l'écriture du Dockerfile jusqu'à la mise "
        "en production via un pipeline d'intégration continue.\n\nCe poste m'intéresse parce qu'il "
        "combine le développement et l'exploitation, deux faces du métier que j'ai appris à ne pas "
        "séparer. Je serais heureux de vous exposer ma démarche lors d'un entretien.\n\n"
        "Je vous prie d'agréer, Madame, Monsieur, mes salutations distinguées."
    ),
    "_mock": True,
}


class LLMError(RuntimeError):
    pass


def _client():
    """Retourne (client, modèle) selon LLM_PROVIDER."""
    provider = provider_name()

    if provider == "azure":
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        if not (endpoint and key and deployment):
            raise LLMError("Variables Azure OpenAI incomplètes")
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=key,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            timeout=60.0,
        )
        return client, deployment

    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise LLMError("OPENAI_API_KEY manquante")
        client = OpenAI(
            api_key=key,
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            timeout=60.0,
        )
        return client, os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    raise LLMError(f"Fournisseur inconnu : {provider}")


def provider_name() -> str:
    return os.getenv("LLM_PROVIDER", "mock").lower()


def analyser(offre: str, profil: str) -> dict:
    """Analyse l'offre face au profil. Mode mock : réponse figée, aucun appel réseau."""
    if provider_name() == "mock":
        return MOCK_RESPONSE

    client, model = _client()
    reponse = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"OFFRE :\n{offre}\n\nPROFIL DU CANDIDAT :\n{profil}",
            },
        ],
        temperature=0.4,
        response_format={"type": "json_object"},
    )
    contenu = reponse.choices[0].message.content
    try:
        return json.loads(contenu)
    except json.JSONDecodeError as exc:
        raise LLMError("Réponse du modèle illisible") from exc
