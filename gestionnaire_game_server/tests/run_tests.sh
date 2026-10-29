#!/bin/bash
# ==============================================================================
# SCRIPT DE TESTS D'INTEGRATION AUTOMATISES (CI / CD DOCKER)
# Valide la disponibilite et la communication inter-conteneurs de bout en bout
# ==============================================================================

set -e

FRONT_URL="${FRONT_URL:-http://front:8080}"
MAX_RETRIES=10
RETRY_DELAY=2

echo "=========================================================="
echo " LANCEMENT DES TESTS D'INTEGRATION (STACK DOCKER CLOUD)"
echo " Cible : ${FRONT_URL}"
echo "=========================================================="

# Fonction d'attente active
wait_for_service() {
    local url=$1
    local name=$2
    echo -n "[WAIT] Attente de disponibilite de ${name}..."
    local count=0
    until curl -s -f "${url}" > /dev/null 2>&1; do
        count=$((count + 1))
        if [ "$count" -ge "$MAX_RETRIES" ]; then
            echo " ECHEC (Timeout apres ${MAX_RETRIES} essais)"
            return 1
        fi
        sleep "$RETRY_DELAY"
    done
    echo " PRET."
}

# 1. Attente du Front Nginx
wait_for_service "${FRONT_URL}/health" "Front-End Nginx"

# 2. Test de la sonde de sante du Front
echo -n "[TEST 1] Verification de la sonde de sante Front Nginx... "
FRONT_HEALTH=$(curl -s "${FRONT_URL}/health")
if echo "$FRONT_HEALTH" | grep -q "healthy"; then
    echo "VALIDE (Sonde OK)"
else
    echo "ECHEC"
    exit 1
fi

# 3. Test du Reverse Proxy vers l'API Back-End
echo -n "[TEST 2] Verification du routage Nginx vers le Back-End (/api/admin/status)... "
BACK_STATUS=$(curl -s "${FRONT_URL}/api/admin/status")
if echo "$BACK_STATUS" | grep -q "backend-core-api"; then
    echo "VALIDE (Proxy operationnel)"
else
    echo "ECHEC"
    exit 1
fi

# 4. Test de la liaison Back-End vers le Serveur de Jeux
echo -n "[TEST 3] Verification de la recuperation des sessions multi-jeux... "
GAMES_DATA=$(curl -s "${FRONT_URL}/api/admin/games")
if echo "$GAMES_DATA" | grep -q "PixelQuest"; then
    echo "VALIDE (Sessions detectees)"
else
    echo "ECHEC"
    exit 1
fi

# 5. Test d'une commande d'administration (POST)
echo -n "[TEST 4] Test d'execution d'une action admin (POST /api/admin/action)... "
ACTION_RESP=$(curl -s -X POST "${FRONT_URL}/api/admin/action" \
    -H "Content-Type: application/json" \
    -d '{"session_id":"game-session-01","player":"Test_Runner","points":25,"action":"add_points"}')

if echo "$ACTION_RESP" | grep -q "Test_Runner"; then
    echo "VALIDE (Score mis a jour)"
else
    echo "ECHEC"
    exit 1
fi

echo "=========================================================="
echo " SUCCES : L'ENSEMBLE DES 4 TESTS SONT CONFORMANTS ET VALIDES"
echo " Code de sortie : 0"
echo "=========================================================="
exit 0
