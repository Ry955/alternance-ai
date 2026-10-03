#!/usr/bin/env bash
# Cree l'infrastructure Azure du projet et deploie une premiere version.
# Usage : bash infra/deploy.sh
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-alternance-ai-rg}"
LOCATION="${LOCATION:-francecentral}"
ACR_NAME="${ACR_NAME:-alternanceacr$RANDOM}"
CA_ENV="${CA_ENV:-alternance-env}"
CA_APP="${CA_APP:-alternance-ai}"
AOAI_NAME="${AOAI_NAME:-alternance-openai-$RANDOM}"
AOAI_DEPLOYMENT="${AOAI_DEPLOYMENT:-gpt-4o-mini}"
IMAGE="alternance-ai:v1"

echo "==> Groupe de ressources"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

echo "==> Container Registry : $ACR_NAME"
az acr create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACR_NAME" \
  --sku Basic \
  --admin-enabled true \
  --output none
LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer --output tsv)

echo "==> Construction de l'image dans ACR"
az acr build --registry "$ACR_NAME" --image "$IMAGE" . --output none

echo "==> Azure OpenAI : $AOAI_NAME"
az cognitiveservices account create \
  --name "$AOAI_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --kind OpenAI \
  --sku S0 \
  --yes --output none

az cognitiveservices account deployment create \
  --name "$AOAI_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --deployment-name "$AOAI_DEPLOYMENT" \
  --model-name gpt-4o-mini \
  --model-version "2024-07-18" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard \
  --output none

AOAI_ENDPOINT=$(az cognitiveservices account show --name "$AOAI_NAME" \
  --resource-group "$RESOURCE_GROUP" --query properties.endpoint --output tsv)
AOAI_KEY=$(az cognitiveservices account keys list --name "$AOAI_NAME" \
  --resource-group "$RESOURCE_GROUP" --query key1 --output tsv)

echo "==> Environnement Container Apps"
az extension add --name containerapp --upgrade --only-show-errors
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
az containerapp env create \
  --name "$CA_ENV" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none

echo "==> Container App"
az containerapp create \
  --name "$CA_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$CA_ENV" \
  --image "$LOGIN_SERVER/$IMAGE" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 5 \
  --cpu 0.5 --memory 1.0Gi \
  --registry-server "$LOGIN_SERVER" \
  --registry-username "$(az acr credential show --name "$ACR_NAME" --query username --output tsv)" \
  --registry-password "$(az acr credential show --name "$ACR_NAME" --query 'passwords[0].value' --output tsv)" \
  --secrets aoai-key="$AOAI_KEY" \
  --env-vars \
      LLM_PROVIDER=azure \
      AZURE_OPENAI_ENDPOINT="$AOAI_ENDPOINT" \
      AZURE_OPENAI_DEPLOYMENT="$AOAI_DEPLOYMENT" \
      AZURE_OPENAI_API_KEY=secretref:aoai-key \
  --output none

FQDN=$(az containerapp show --name "$CA_APP" --resource-group "$RESOURCE_GROUP" \
  --query properties.configuration.ingress.fqdn --output tsv)

echo
echo "Application en ligne : https://$FQDN"
echo
echo "Secrets a enregistrer dans GitHub (Settings > Secrets and variables > Actions) :"
echo "  ACR_NAME                = $ACR_NAME"
echo "  AZURE_RESOURCE_GROUP    = $RESOURCE_GROUP"
echo "  CONTAINERAPP_NAME       = $CA_APP"
echo "  AZURE_CREDENTIALS       = sortie de la commande ci-dessous"
echo
echo "az ad sp create-for-rbac --name alternance-ci --role Contributor \\"
echo "  --scopes \$(az group show --name $RESOURCE_GROUP --query id -o tsv) --sdk-auth"
