# ==============================================================================
# CONTENEUR CONTROLEUR D'AUTOSCALING DOCKER SWARM
# Image minimale basee sur Alpine Linux avec acces au socket Docker
# ==============================================================================

FROM alpine:3.20

# 1. Installation de docker-cli et des outils de calcul
RUN apk update && \
    apk add --no-cache docker-cli bash curl grep gawk && \
    rm -rf /var/cache/apk/*

WORKDIR /app

# 2. Copie et attribution des permissions d'execution
COPY autoscale.sh /app/autoscale.sh
RUN chmod 755 /app/autoscale.sh

ENTRYPOINT ["/bin/sh", "/app/autoscale.sh"]
