# GCP Deployment

This app is packaged for Cloud Run.

## Required Services

- Cloud Run
- Cloud SQL for PostgreSQL
- Vertex AI
- Secret Manager
- Artifact Registry

## Runtime Environment

Set these variables on the Cloud Run service:

```env
APP_ENV=production
AUTO_INIT_DB=true
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@/DB_NAME?host=/cloudsql/PROJECT:REGION:INSTANCE
TELEGRAM_BOT_TOKEN=...
TELEGRAM_SECRET_TOKEN=...
GCP_PROJECT_ID=...
GCP_REGION=us-central1
KHAYA_API_KEY=...
YOUTUBE_PROXY_URL=http://USER:PASSWORD@HOST:PORT
TTS_TEMPO=1.0
```

Use Secret Manager for tokens, API keys, and database credentials.
Use a rotating residential proxy for `YOUTUBE_PROXY_URL`; datacenter proxies are commonly blocked by YouTube.

The Cloud Run service account needs at least:

- Cloud SQL Client
- Vertex AI User
- Secret Manager Secret Accessor, if secrets are mounted from Secret Manager

## Build And Deploy

```bash
gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT/REPOSITORY/yt-bot:latest

gcloud run deploy yt-bot \
  --image REGION-docker.pkg.dev/PROJECT/REPOSITORY/yt-bot:latest \
  --region REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances PROJECT:REGION:INSTANCE \
  --service-account SERVICE_ACCOUNT_EMAIL
```

## Health Checks

- `/healthz` is a lightweight liveness check.
- `/readyz` verifies database connectivity.

## Notes

`AUTO_INIT_DB=true` uses SQLAlchemy to create missing tables at startup. This is acceptable for the current MVP, but production should move to Alembic migrations before schema changes become frequent.
