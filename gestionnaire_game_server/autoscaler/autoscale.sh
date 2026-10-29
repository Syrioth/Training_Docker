#!/bin/sh
# ==============================================================================
# CONTROLEUR D'AUTOSCALING DYNAMIQUE DOCKER SWARM (HPA)
# Surveille la consommation CPU du service backend et ajuste les replicas
# ==============================================================================

SERVICE="back"
STACK_NAME="${STACK_NAME:-cloud_game}"
FULL_SERVICE="${STACK_NAME}_${SERVICE}"
MIN_REPLICAS=1
MAX_REPLICAS=5
CPU_SCALE_UP=70
CPU_SCALE_DOWN=15
SLEEP=10

echo "[AUTOSCALER] Demarrage de la surveillance pour ${FULL_SERVICE}"

while true; do
  REPLICAS=$(docker service ps ${FULL_SERVICE} --filter desired-state=running -q 2>/dev/null | wc -l)
  
  if [ "$REPLICAS" -gt 0 ]; then
    TOTAL_CPU=$(docker stats --no-stream --format "{{.Name}} {{.CPUPerc}}" 2>/dev/null \
      | grep "${FULL_SERVICE}" \
      | awk '{gsub(/%/,"",$2); sum+=$2} END {print int(sum)}')
    
    TOTAL_CPU=${TOTAL_CPU:-0}
    echo "$(date '+%Y-%m-%d %H:%M:%S') - [${FULL_SERVICE}] CPU=${TOTAL_CPU}% | Replicas=${REPLICAS}"

    # Declenchement du Scale UP
    if [ "$TOTAL_CPU" -gt "$CPU_SCALE_UP" ] && [ "$REPLICAS" -lt "$MAX_REPLICAS" ]; then
      NEW=$((REPLICAS + 1))
      echo "[AUTOSCALER] Alerte charge CPU (${TOTAL_CPU}% > ${CPU_SCALE_UP}%) -> Scale UP vers ${NEW} replicas"
      docker service scale ${FULL_SERVICE}=$NEW
    fi

    # Declenchement du Scale DOWN
    if [ "$TOTAL_CPU" -lt "$CPU_SCALE_DOWN" ] && [ "$REPLICAS" -gt "$MIN_REPLICAS" ]; then
      NEW=$((REPLICAS - 1))
      echo "[AUTOSCALER] Retour a la normale (${TOTAL_CPU}% < ${CPU_SCALE_DOWN}%) -> Scale DOWN vers ${NEW} replicas"
      docker service scale ${FULL_SERVICE}=$NEW
    fi
  fi

  sleep $SLEEP
done
