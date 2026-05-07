# Deployment

The app is packaged for Cloud Run.

## Required Services

- Cloud Run
- Cloud SQL for PostgreSQL
- Vertex AI
- Secret Manager
- Artifact Registry

## Environment Variables

Set these on the Cloud Run service:

```env
APP_ENV=production
AUTO_INIT_DB=true
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@/DB_NAME?host=/cloudsql/PROJECT:REGION:INSTANCE
TELEGRAM_BOT_TOKEN=...
TELEGRAM_SECRET_TOKEN=...
GCP_PROJECT_ID=...
GCP_REGION=us-central1
KHAYA_API_KEY=...
TTS_TEMPO=1.0
LOG_LEVEL=INFO
```

Use Secret Manager for tokens, API keys, and database credentials.

## IAM

The Cloud Run service account needs:

- Cloud SQL Client
- Vertex AI User
- Secret Manager Secret Accessor (if mounting secrets)

## Build and Deploy

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

- `/healthz` — liveness check
- `/readyz` — database connectivity check

## Notes

`AUTO_INIT_DB=true` creates tables at startup via SQLAlchemy. Migrate to Alembic before schema changes become frequent.
