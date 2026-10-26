# ==============================================================================
# Dockerfile : back
# API Backend - Architecture Docker Cloud
# ==============================================================================

# 1. Image de base minimale Alpine Linux 3.20 (légèreté et sécurité)
FROM alpine:3.20

LABEL maintainer="Étudiant Master M1" \
      description="API Backend Hello World personnalisée"

# 2. Arguments au build et variables d'environnement au run
ARG DEFAULT_PORT=8081
ENV PORT=${DEFAULT_PORT} \
    SERVICE_NAME="backend-core-api" \
    GAME_SERVER_URL="http://game-server:8082" \
    PYTHONUNBUFFERED=1

# 3. Manipulations sur l'OS et installation des dépendances
# - Installation de python3 et curl
# - Nettoyage du cache des paquets
RUN apk update && \
    apk add --no-cache python3 curl && \
    rm -rf /var/cache/apk/*

# 4. Sécurité OS : Utilisateur non-root backuser (UID 1002)
RUN addgroup -g 1002 -S backgroup && \
    adduser -u 1002 -S -D -h /app -s /sbin/nologin -G backgroup backuser

WORKDIR /app

# 5. Copie du code applicatif et droits non-root
COPY app.py /app/app.py
RUN chown -R backuser:backgroup /app && \
    chmod 755 /app/app.py

# 6. Exécution en utilisateur non-root
USER backuser

EXPOSE 8081

# 7. Healthcheck Docker
HEALTHCHECK --interval=5s --timeout=3s --start-period=2s --retries=3 \
  CMD curl -f http://localhost:8081/health || exit 1

# 8. ENTRYPOINT en Exec Form ["executable", "param"] pour être PID 1
ENTRYPOINT ["python3", "/app/app.py"]
