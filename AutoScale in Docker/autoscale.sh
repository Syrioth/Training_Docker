#!/bin/sh
# ============================
# Simple host-based Swarm autoscaler
# for 'web' service in your stack
# ============================

# ---- CONFIG ----
SERVICE="web"             # Must match the service name in your stack
STACK_NAME="demo"         # Replace if you deployed with a stack name
MIN_REPLICAS=1
MAX_REPLICAS=5
CPU_SCALE_UP=80           # percent
CPU_SCALE_DOWN=10        # percent
SLEEP=10                  # seconds between checks

echo "Starting autoscaler for ${STACK_NAME}_${SERVICE}"

while true; do
  # Get all tasks for this service that are running
  REPLICAS=$(docker service ps ${STACK_NAME}_${SERVICE} \
    --filter desired-state=running -q | wc -l)

  # Get total CPU usage across all containers of this service
  TOTAL_CPU=$(docker stats --no-stream --format "{{.Name}} {{.CPUPerc}}" \
    | grep "${STACK_NAME}_${SERVICE}" \
    | awk '{gsub(/%/,"",$2); sum+=$2} END {print int(sum)}')

  echo "$(date) - CPU=${TOTAL_CPU}% | replicas=${REPLICAS}"

  # Scale up if CPU > threshold
  if [ "$TOTAL_CPU" -gt "$CPU_SCALE_UP" ] && [ "$REPLICAS" -lt "$MAX_REPLICAS" ]; then
    NEW=$((REPLICAS + 1))
    echo "🔥 Scaling UP → $NEW replicas"
    docker service scale ${STACK_NAME}_${SERVICE}=$NEW
  fi

  # Scale down if CPU < threshold
  if [ "$TOTAL_CPU" -lt "$CPU_SCALE_DOWN" ] && [ "$REPLICAS" -gt "$MIN_REPLICAS" ]; then
    NEW=$((REPLICAS - 1))
    echo "⬇️ Scaling DOWN → $NEW replicas"
    docker service scale ${STACK_NAME}_${SERVICE}=$NEW
  fi

  sleep $SLEEP
done
