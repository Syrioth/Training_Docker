# ==============================================================================
# Dockerfile : front
# Serveur Web Frontend - Architecture Docker Cloud
# ==============================================================================

# 1. Image de base minimale Alpine Linux 3.20 (légèreté et sécurité)
FROM alpine:3.20

LABEL maintainer="Étudiant Master M1" \
      description="Front-End Hello World personnalisé"

# 2. Arguments au build et variables d'environnement au run
ARG DEFAULT_PORT=8080
ENV PORT=${DEFAULT_PORT} \
    BACKEND_URL="http://back:8081" \
    PYTHONUNBUFFERED=1

# 3. Manipulations sur l'OS et installation des dépendances
# - Installation de python3 et curl
# - Nettoyage du cache des paquets
RUN apk update && \
    apk add --no-cache python3 curl && \
    rm -rf /var/cache/apk/*

# 4. Sécurité OS : Utilisateur non-root frontuser (UID 1003)
RUN addgroup -g 1003 -S frontgroup && \
    adduser -u 1003 -S -D -h /app -s /sbin/nologin -G frontgroup frontuser

WORKDIR /app

# 5. Copie du code applicatif et des fichiers statiques
COPY server.py /app/server.py
COPY static /app/static
RUN chown -R frontuser:frontgroup /app && \
    chmod 755 /app/server.py

# 6. Exécution en utilisateur non-root
USER frontuser

EXPOSE 8080

# 7. Healthcheck Docker
HEALTHCHECK --interval=5s --timeout=3s --start-period=2s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# 8. ENTRYPOINT en Exec Form ["executable", "param"] pour être PID 1
ENTRYPOINT ["python3", "/app/server.py"]
