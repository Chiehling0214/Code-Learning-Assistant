# docker/

Supplementary Docker assets and notes.

The primary orchestration lives in the repository-root
[`docker-compose.yml`](../docker-compose.yml). Per-service build files are kept
next to their code:

- Backend image: [`backend/Dockerfile`](../backend/Dockerfile)
- Frontend image: [`frontend/Dockerfile`](../frontend/Dockerfile) (multi-stage:
  `dev` target for compose, `prod` target serves static assets via Nginx)

This folder is reserved for future shared Docker assets (e.g. a production
compose override, database init scripts, or a reverse-proxy config). See
[docs/08_DEPLOYMENT.md](../docs/08_DEPLOYMENT.md).
