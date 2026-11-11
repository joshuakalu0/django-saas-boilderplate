# Project 2: Multi-Tenant SaaS Starter (Django)

Production-style multi-tenant SaaS built with Django, `django-tenants`, DRF, HTMX, Celery, Redis, PostgreSQL, Stripe, Docker, and Nginx.

## What this project delivers

- Shared public host for registration, login, verification, and password reset
- Tenant subdomains with schema-based PostgreSQL isolation
- Server-rendered workspace UI with Django templates and HTMX-ready foundations
- REST API under `/api/v1/` with JWT and API key auth
- Swagger UI at `/api/docs/` and Redoc at `/api/docs/redoc/`
- Stripe checkout + customer portal wiring
- Celery tasks for email delivery, webhook handling, and cleanup jobs
- Docker-first runtime with app, worker, beat, postgres, redis, mailpit, and nginx

## Local host model

- Public host: `http://app.lvh.me`
- Tenant host pattern: `http://{tenant}.lvh.me`
- Mail inbox preview: `http://localhost:8025`
- Swagger UI: `http://app.lvh.me/api/docs/`

`lvh.me` resolves to `127.0.0.1`, which makes it a convenient local subdomain strategy for tenant development.

## Repo structure

- `config`: settings split, URL routing, health endpoints, WSGI/ASGI, Celery app
- `common`: enums, shared helpers, middleware, response helpers, base mixins
- `tenants`: organization/domain models, tenant middleware, bootstrap command
- `accounts`: custom user model, verification/reset flows, public auth pages
- `workspace`: tenant-scoped members, invitations, projects, audit log, dashboard pages
- `billing`: shared-schema subscriptions, API keys, checkout and portal views
- `api`: serializers, auth classes, permissions, REST endpoints, docs routes
- `docker`: app entrypoint and nginx config

## Quick start

1. Copy `.env.example` to `.env`.
2. Start the stack:

```bash
docker compose up --build
```

3. Open:
   - `http://app.lvh.me`
   - `http://localhost:8025`
   - `http://app.lvh.me/api/docs/`

The app entrypoint runs shared-schema migrations, collects static files, and ensures the public tenant exists.

## Running checks

If `uv` is installed locally:

```bash
uv sync --all-groups
uv run python manage.py check
uv run pytest
```

If you prefer Docker:

```bash
docker compose run --rm app python manage.py check
docker compose run --rm app pytest
```

## Authentication model

### Web app

- Django session auth
- Public-host login and registration
- Shared cookie domain for local subdomain navigation

### API

- JWT bearer access tokens
- Refresh token via secure cookie by default
- Optional refresh token in response body when the client sends `X-Return-Refresh-Token: true`
- Organization-scoped API keys via `Authorization: Bearer <api-key>`

## Tenant routing

- Production routing is hostname-first
- Local and API fallback supports `X-Tenant-Slug`
- Public tenant defaults to `app.lvh.me`
- New tenant domains follow `{slug}.lvh.me`

## Billing and limits

- Supported plans: `FREE`, `PRO`, `ENTERPRISE`
- FREE defaults:
  - `max_members = 3`
  - `max_projects = 5`
- Limits are enforced in the service layer for web and API flows

## CI/CD baseline

The project includes a dedicated GitHub Actions workflow at `.github/workflows/project2-saas-django.yml` that:

- installs Python 3.12 and `uv`
- provisions PostgreSQL and Redis
- runs `migrate_schemas --shared`
- runs Django checks and pytest
- verifies the Docker image builds successfully

## Environment variables

Core variables are documented in `.env.example`. The most important ones are:

- `DJANGO_SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `DJANGO_PUBLIC_HOST`
- `DJANGO_SESSION_COOKIE_DOMAIN`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`

## Current defaults

- Email/password auth only in v1
- Public marketing site intentionally excluded
- Stripe gracefully falls back to local URLs when keys are not configured
- Comments stay focused on non-obvious tenancy, auth, and billing behavior

