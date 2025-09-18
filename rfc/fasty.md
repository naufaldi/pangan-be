# FastAPI Service Notes

## High-Level Overview
- `app/main.py` creates the FastAPI instance, wires logging, lifespan, and CORS, then mounts the aggregated router from `app/api/router.py`.
- The project follows a clean architecture split:
  - `app/api`: HTTP adapters (routers + Pydantic response schemas).
  - `app/usecases`: application services and DTO/port definitions that hide infrastructure details.
  - `app/core`: domain models expressed as immutable dataclasses.
  - `app/infra`: concrete adapters (SQLAlchemy repositories, HTTP upstream client, seeding helpers).
  - `app/common`: cross-cutting utilities (settings, structured logging, checksums).
  - `app/lifespan.py`: async context manager that warms up the DB and exposes `is_ready()` for readiness probes.
- `scripts/dev.py` is the developer CLI for linting, running uvicorn, seeding dimension tables, and orchestrating the ingestion pipeline.

## Main Application Composition (`app/main.py`)
- Imports: pulls FastAPI, CORS middleware, project settings/logging helpers, the lifespan context, and the aggregated `api_router`.
- Startup wiring:
  - `settings = get_settings()` loads environment-driven config once; `setup_logging(settings.LOG_LEVEL)` installs JSON logging early so subsequent logs use consistent structure.
  - A module-level logger (`logging.getLogger("pangan")`) is created for request middleware.
- FastAPI instance:
  - Instantiated with title/version/description metadata and `lifespan=lifespan_context` so startup/shutdown hooks run through the async context manager in `app/lifespan.py`.
  - CORS middleware allows any origin, credentials, headers, and methods (development-friendly, tighten for prod).
  - The centralized router (`api_router`) is included, automatically mounting every sub-router registered in `app/api/router.py`.
- Request logging middleware:
  - Runs on every HTTP request, reads an optional `X-Request-ID`, and logs structured `request_start` and `request_end` events with method/path/status.
  - Uses `call_next` to forward to the next handler, then logs the response status before returning it, enabling correlation-friendly logs without altering responses.

## Request Flow (Health Endpoints Example)
1. `GET /health/healthz` or `/health/readyz` hits the router in `app/api/health.py`.
2. The route calls into `app/usecases/health_service.py`, which returns a `HealthStatus` domain object.
3. Responses are converted to plain JSON (RORO style) and validated against `app/api/schemas.py`.
4. Readiness additionally checks `app.lifespan.is_ready()` and performs a lightweight `SELECT 1` using a fresh SQLAlchemy engine.

## Lifespan & Readiness
- `lifespan_context` sets the timezone, performs a short warmup sleep, and runs `SELECT 1` if `DATABASE_URL` is configured.
- `_ready` flips to `True` once warmup finishes; `/health/readyz` returns `503` until then or when DB checks fail.
- `get_engine()` in `app/infra/db.py` currently creates a new engine per call (simple but a bit heavy under load); caching the engine is a future optimization.

## Configuration & Logging
- Configuration uses `pydantic_settings.BaseSettings` (`app/common/settings.py`). Values load from environment variables or `.env`.
- Logging is JSON-formatted via `python-json-logger` and initialized in `app/main.py::setup_logging()`.
- CORS is open (`*`) in development; tighten `allow_origins` before production.

## Database Layer
- SQLAlchemy 2.0 declarative models live in `app/infra/models.py`:
  - `Commodity`, `Province`, `PriceMonthly` with constraints for uniqueness and valid periods.
- `app/infra/db.py` exposes `Base`, `get_engine()`, and `get_db_session()` for dependency injection.
- Repository adapters under `app/infra/repositories/` return functional ports defined in `app/usecases/ports.py`:
  - `make_price_repository()` supports bulk UPSERT with conflict detection and provides pagination queries.
  - `make_commodity_repository()` and `make_province_repository()` expose sorted `list_all()` helpers.
- Seeding helpers (`app/infra/seeding.py`) upsert dimension tables and power the `python scripts/dev.py seed-dimensions` command.

## Ingestion Pipeline
- The core ingestion orchestration lives in `app/usecases/ingest.py`:
  - Validates `FetchParams`, fetches upstream data through an `UpstreamClientPort`, normalizes monthly buckets, computes deterministic checksums, and upserts rows via `PriceRepositoryPort`.
  - Guard clauses reject invalid year or date ranges early.
  - Structured logging captures timings for fetch/normalize/checksum/upsert phases.
- Upstream HTTP client (`app/infra/http/upstream.py`) uses `httpx.Client` with retry/backoff logic and supports a mock payload for offline development.
- Schemas in `app/usecases/schemas.py` ensure upstream payload integrity and normalized row shape.
- CLI entry points inside `scripts/dev.py` wrap these flows (`scrape-test`, `ingest`) with options for mock data, payload persistence, and summary outputs.

## API Surface Today
- Only health routes are exposed right now (`/health/healthz`, `/health/readyz`).
- Additional routers should be added to `app/api/router.py`, then wired into `app/main.py` automatically via inclusion.

## Observed Gaps & Follow-Ups
- Engine creation on each readiness check is acceptable for low traffic but should eventually reuse a singleton or AsyncEngine pool.
- `HealthService` is class-based; future refactors may convert it to simple functions plus dependency wiring to align with functional guidelines.
- There is no API surface for querying cached price data yet. Implementing read endpoints will require wiring price repositories through FastAPI dependencies.
- Alembic migrations exist (`alembic/`, `migrations/`), but ensure they stay aligned with the SQLAlchemy models when schema evolves.

## Getting Started Checklist
- Install dependencies: `pip install -r requirements.txt` (or use `poetry install` if the project migrates to Poetry; `pyproject.toml` already lists packages).
- Provide `DATABASE_URL`; leaving it empty defaults to SQLite (`dev.db`) for quick tests.
- Run local server: `uvicorn app.main:app --reload --port 8000`.
- Use `scripts/dev.py quality` for lint/format hooks and `scripts/dev.py ingest` (with `--mock`) to exercise the ingestion flow end-to-end.
