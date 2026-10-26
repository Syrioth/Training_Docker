# ==============================================================================
# Dockerfile : game-server
# Serveur Web Spécialisé (Serveur de Jeu) - Architecture Docker Cloud
# ==============================================================================

# 1. Image de base minimale Alpine Linux 3.20 (sécurité et légèreté)
FROM alpine:3.20

LABEL maintainer="Étudiant Master M1" \
      description="Serveur web / jeu Hello World personnalisé"

# 2. Arguments au build et variables d'environnement au run
ARG DEFAULT_PORT=8082
ENV PORT=${DEFAULT_PORT} \
    SERVICE_NAME="game-web-server" \
    PYTHONUNBUFFERED=1

# 3. Manipulations sur l'OS et installation des dépendances
# - Installation de python3 (runtime) et curl (requis pour HEALTHCHECK)
# - Purge du cache des paquets apk
RUN apk update && \
    apk add --no-cache python3 curl && \
    rm -rf /var/cache/apk/*

# 4. Sécurité OS : Création de l'utilisateur non-root gameuser (UID 1001)
RUN addgroup -g 1001 -S gamesquad && \
    adduser -u 1001 -S -D -h /app -s /sbin/nologin -G gamesquad gameuser

WORKDIR /app

# 5. Copie du code applicatif et droits non-root
COPY server.py /app/server.py
RUN chown -R gameuser:gamesquad /app && \
    chmod 755 /app/server.py

# 6. Exécution en tant qu'utilisateur non-root
USER gameuser

EXPOSE 8082

# 7. Healthcheck Docker pour garantir l'ordre de démarrage
HEALTHCHECK --interval=5s --timeout=3s --start-period=2s --retries=3 \
  CMD curl -f http://localhost:8082/health || exit 1

# 8. ENTRYPOINT en Exec Form ["executable", "param"] pour être PID 1 et intercepter SIGTERM
ENTRYPOINT ["python3", "/app/server.py"]
