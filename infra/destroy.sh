#!/usr/bin/env bash
# Supprime toutes les ressources du projet pour arreter la facturation.
set -euo pipefail
RESOURCE_GROUP="${RESOURCE_GROUP:-alternance-ai-rg}"
az group delete --name "$RESOURCE_GROUP" --yes --no-wait
echo "Suppression de $RESOURCE_GROUP lancee."
