# ==============================================================================
# CONTENEUR DE TESTS D'INTEGRATION CI/CD (MASTER 1 DOCKER CLOUD)
# Valide la conformite et les flux inter-services sans image Docker Hub metier
# ==============================================================================

FROM alpine:3.20

# 1. Installation des utilitaires de test reseau
RUN apk update && \
    apk add --no-cache bash curl jq && \
    rm -rf /var/cache/apk/*

# 2. Principe de moindre privilege : utilisateur dedie non-root
RUN addgroup -g 1004 -S testgroup && \
    adduser -u 1004 -S -D -h /app -s /sbin/nologin -G testgroup testuser

WORKDIR /app

# 3. Copie et attribution des permissions d'execution
COPY run_tests.sh /app/run_tests.sh
RUN chmod 755 /app/run_tests.sh && \
    chown -R testuser:testgroup /app

USER testuser

ENTRYPOINT ["/bin/bash", "/app/run_tests.sh"]
