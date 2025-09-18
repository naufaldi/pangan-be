### RFC: Pangan Indonesia Data Cache & API (Python)

## Objective
- **Goal**: Ingest price data from the government API, cache it in our DB, and expose a reliable, well-documented API with higher availability and predictable latency.
- **KPIs**: 99.9% uptime for our API, P50 latency < 150ms, successful weekly refreshes, monthly rebuild for previous month.

## Scope
- **In-scope**: Data ingestion, storage, scheduled refresh, public read API, basic observability, basic docs.
- **Out-of-scope**: UI frontend, admin panel, complex analytics (beyond basic aggregations), multi-region writes.

## Plan Update — Ingest-First Sequence
- Rationale: validate upstream fetch and database persistence before building the public API.
- Steps:
  1. Implement `fetch_and_upsert` to normalize month-bucketed payloads and perform idempotent upsert using raw SQL for schema alignment and deterministic behavior.
  2. Add strict Pydantic validation for upstream payload shape and normalized rows.
  3. Provide CLI `scripts/dev.py ingest` with args: `start_year`, `end_year`, `period_start`, `period_end`, `level_harga_id`, optional `province_id`, and flags `--mock`, `--dry-run`, `--save`.
  4. Run one-shot ingest for a known-good window; seed dimensions if missing.
  5. Verify DB is populated: non-zero row counts; re-run shows `unchanged` grows (idempotency); spot-check with `SELECT`.
  6. Only after acceptance, implement `GET /commodities`, `GET /provinces`, and `GET /prices` (filters + pagination).
- Acceptance to proceed to API:
  - Ingest yields non-zero `inserted` or `unchanged`.
  - Unique-key idempotency confirmed on re-run (increased `unchanged`).
  - Sample queries for the window return expected rows.

## Users & Flows
- **Data Ops (internal)**
  - **Trigger ad-hoc refresh**: Manually run an ingest for a specific date range if upstream corrected data.
  - **Monitor jobs**: Check logs/metrics for failed pulls and retry counts.
  - **Health checks**: Verify API and DB are healthy.
- **Public API Consumers (external)**
  - **Query prices**: Filter by `commodity_id`, `province_id`, `level_harga_id`, date range.
  - **Discover metadata**: List commodities and provinces.
  - **Docs access**: Browse OpenAPI/Swagger and examples.

## Tech Stack
- **Language/Runtime**: Python 3.12
- **API**: FastAPI + Uvicorn
- **HTTP Client**: `httpx` (timeout, retries)
- **DB**: PostgreSQL 16 (`SQLAlchemy` + `psycopg[binary]`)
- **Scheduling**: APScheduler (in-app) + OS cron as safety net
- **Container**: Docker + Compose (deployment only)
- **Time/Locale**: `Asia/Jakarta`
- **Validation**: Pydantic models for incoming/outgoing schemas
- **Observability**: Structured logging (JSON), simple counters, health endpoints

### Development vs Deployment Strategy
- **Local Development**: Run Python directly with virtual environment
  - Use `python -m uvicorn app.main:app --reload` for development
  - No Docker overhead for faster iteration
  - Direct debugging and hot reload capabilities
- **Production Deployment**: Docker containers on VPS
  - Use Docker for consistent deployment environment
  - Container orchestration with docker-compose for multi-service setup
  - Proper isolation and resource management

## Source API (reference)
- Base: `https://api-panelhargav2.badanpangan.go.id/api/front/harga-pangan-bulanan-v2`
- Core params: `start_year`, `end_year`, `period_date=DD/MM/YYYY - DD/MM/YYYY`, `province_id`, `level_harga_id`
- Headers: Accept JSON, referer/origin same-site, realistic user-agent.

## Data Model (relational)
- `commodities(id text primary key, name text not null)`
- `provinces(id text primary key, name text not null)`
- `prices_monthly(
  id bigserial primary key,
  commodity_id text references commodities(id),
  province_id text references provinces(id),
  level_harga_id int not null,
  period_start date not null,
  period_end date not null,
  price numeric not null,
  unit text not null,
  checksum text,
  inserted_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(commodity_id, province_id, level_harga_id, period_start, period_end)
)`

## Public API (initial)
Note: Implement these only after ingestion acceptance criteria are met.
- `GET /prices`
  - Query: `commodity_id?`, `province_id?`, `level_harga_id` (required), `period_start` (YYYY-MM-DD), `period_end` (YYYY-MM-DD), `limit?`, `offset?`
  - Response: rows with commodity/province names, price, unit, period, level.
- `GET /commodities`
- `GET /provinces`
- `GET /healthz` and `GET /readyz`
- Auto docs at `/docs` (Swagger UI) and `/openapi.json`.

## Architecture
- **FastAPI app**: Serves public API and hosts APScheduler jobs.
- **Ingest service (function/module)**: Pulls from source API with backoff, validates shape, transforms to rows, upserts to Postgres using the unique key for idempotency.
- **Schedulers**:
  - Weekly refresh: Every Monday 01:00 Asia/Jakarta for current month.
  - Monthly rebuild: 1st day 02:00 Asia/Jakarta for previous month.
  - OS cron mirrors these schedules to recover from app restarts.
- **Resilience**: Timeouts, exponential backoff (1,2,4,8,16s), circuit-break style short-circuit after repeated upstream failures, structured error logs with sample payloads on schema mismatch.

## Risks & Mitigations
- **Upstream format changes**: Strict Pydantic schema; fail fast and alert; log sample payload.
- **Legal/ToS**: If redistribution of raw is restricted, expose only aggregates (mean/median, deltas); keep raw internal.
- **Container restarts**: Duplicate schedules via cron; idempotent upsert by unique key.
- **Late upstream updates**: Monthly rebuild ensures drift correction.

## Phased Roadmap & Todo

### Phase 0 — Repo & Environment
- Create repository structure (`app/`, `rfc/`, `compose.yml`, `Dockerfile`).
- Add FastAPI skeleton, health endpoints, config (`DATABASE_URL`, `TZ`).
- Add dependencies: `fastapi`, `uvicorn[standard]`, `SQLAlchemy`, `psycopg[binary]`, `httpx`, `apscheduler`, `pydantic`.
- Configure logging (JSON), settings via environment.
- **Development**: Run with `python -m uvicorn app.main:app --reload --port 8000`
- **Production**: Deploy using Docker containers on VPS

### Phase 1 — Database & Models
- Development: use local PostgreSQL; Production: Dockerized PostgreSQL.
- Implement schema via Alembic with SQL-first migrations (DDL in migrations).
- Create unique constraints and foreign keys per schema above.
- Seed static dimensions: commodities and provinces (from first ingest pass if necessary).
- **Development**: Use local PostgreSQL instance
- **Production**: Deploy PostgreSQL in Docker containers on VPS

### Phase 2 — Ingestion & Idempotent Upsert
- Implement `fetch_and_upsert(start_year, end_year, period_start, period_end, level_harga_id, province_id?)`.
- Build request with proper headers, retries/backoff, and timeouts.
- Parse/validate payload, normalize units, compute `checksum` for change detection.
- Upsert into Postgres using unique key; update when checksum differs.
- CLI/admin endpoint to trigger on-demand ingest:
  - CLI: `scripts/dev.py ingest` args: `start_year`, `end_year`, `period_start`, `period_end`, `level_harga_id`, optional `province_id`; flags: `--mock`, `--dry-run`, `--save`.
- Acceptance (gate to Phase 3):
  - One-shot ingest yields non-zero `inserted` or `unchanged`.
  - Re-running same window increases `unchanged` (idempotency).
  - Manual `SELECT` spot-checks return expected rows.
- **Development**: Test ingestion with local database and mock data
- **Production**: Run ingestion jobs in Docker containers with real upstream data

### Phase 3 — Public API Endpoints
- Prerequisite: Phase 2 acceptance criteria satisfied.
- Implement `GET /prices` with filters, pagination, sorting by `period_start DESC` default.
- Implement `GET /commodities`, `GET /provinces`.
- Add OpenAPI tags, examples; enable Swagger UI at `/docs`.
- Add input validation and 400/422 handling.
- **Development**: Test endpoints with `python -m uvicorn` and local database
- **Production**: Deploy API in Docker containers with production database

### Phase 4 — Scheduling & Reliability
- Add APScheduler jobs for weekly refresh and monthly rebuild.
- Add OS cron entries as redundancy; document how to install on host.
- Implement exponential backoff and simple circuit breaker counters.
- Add idempotency guards to avoid duplicate rows on retries.
- **Development**: Test scheduling with local database and mock external calls
- **Production**: Run scheduled jobs in Docker containers with real data and monitoring

### Phase 5 — Observability & Ops
- Add `GET /healthz`, `GET /readyz` checks (DB `SELECT 1`, simple `GET /prices?limit=1`).
- Structured logs with correlation IDs; log upstream error rates.
- Basic metrics: job success/failure counters, last successful run timestamps.
- Alerting hooks (placeholder to integrate with Slack/Email later).
- **Development**: Monitor logs and metrics locally with `python -m uvicorn`
- **Production**: Deploy monitoring stack in Docker with centralized logging

### Phase 6 — Hardening & Docs
- Load-test read endpoints to verify latency targets.
- Document API usage with examples and curl snippets.
- Add rate limiting guidance (optional) and caching headers (ETag/Last-Modified for stable windows).
- Security review (input validation, headers, error leakage).
- **Development**: Test performance and security locally with `python -m uvicorn`
- **Production**: Deploy hardened application in Docker with security measures

## Acceptance Criteria
- Weekly refresh and monthly rebuild run successfully for a full cycle.
- Public API stable under typical load; returns correct filtered datasets.
- OpenAPI available at `/openapi.json`; Swagger at `/docs`.
- Data duplicates prevented by unique key; updates applied when checksum changes.
- Clear runbook for on-demand backfill and troubleshooting.

## Open Questions
- Do we need aggregates-only mode for legal compliance from day one?
- Should we store and expose both raw and aggregated endpoints?



curl 'https://api-panelhargav2.badanpangan.go.id/api/front/harga-pangan-bulanan-v2?start_year=2023&end_year=2025&period_date=29%2F08%2F2025%20-%2029%2F08%2F2025&province_id=&level_harga_id=3' \
  -H 'Accept: application/json' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'DNT: 1' \
  -H 'Origin: https://panelharga.badanpangan.go.id' \
  -H 'Referer: https://panelharga.badanpangan.go.id/' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-site' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Chromium";v="139", "Not;A=Brand";v="99"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"'

  

## Upstream Response Mapping & Normalization

- Year buckets: `data.{YYYY}` → array of commodity records for that year.
- Commodity fields:
  - `Komoditas_id` → `commodity_id` (store as text)
  - `Komoditas` → `commodities.name`
  - `background` → optional `commodities.asset_url`
  - `Tahun` → year sanity check vs bucket key
  - `today_province_price.satuan` → `unit` (store verbatim; examples: `Rp./Kg`, `Rp/kg`, `Rp/Liter`)
- Monthly values on each commodity record:
  - Month keys: `Jan, Feb, Mar, Apr, Mei, Jun, Jul, Agu, Sep, Okt, Nov, Des`
  - Mapping to month numbers: `{"Jan":1,"Feb":2,"Mar":3,"Apr":4,"Mei":5,"Jun":6,"Jul":7,"Agu":8,"Sep":9,"Okt":10,"Nov":11,"Des":12}`
  - For each present month value, create one row in `prices_monthly` with:
    - `level_harga_id` = from `request_data.level_harga_id`
    - `period_start` = first day of month; `period_end` = last day of month (timezone `Asia/Jakarta`)
    - `price` = month value; `unit` = from `satuan`
    - `province_id` = sentinel `'NATIONAL'` by default (see Decisions) unless a province-specific ingest is implemented
- Idempotency and change detection:
  - Unique key: `(commodity_id, province_id, level_harga_id, period_start, period_end)`
  - `checksum` = stable hash of `(price, unit, level_harga_id, period_start, period_end, commodity_id)` to detect updates

### Optional structures (not stored in `prices_monthly`)
- `today_province_price.zona` and `setting_harga` (HET/HAP; zonasi; time-ranged): useful for reference/analytics.
  - If persisted, use table `price_settings(
    id bigint pk, commodity_id text, level_harga_id int, zona text, type int,
    harga_provinsi_min text, harga_kota_min text, start_date date, end_date date,
    type_description text, type_zonasi int, type_zonasi_description text,
    created_at timestamptz, updated_at timestamptz
  )`.
  - This table is independent of monthly price facts.

## Current Implementation Status (Phase 4A In Progress)

### ✅ **COMPLETED PHASES**
- **Phase 2**: Complete data ingestion pipeline with real upstream API
- **Phase 3**: Full API implementation with GET /prices, GET /commodities, GET /provinces
- **Phase 4A (Week 1)**: ✅ **Level 1 (Producer) data successfully ingested**
  - 145 records added for 2024 producer prices
  - 13 producer-level commodities covered
  - API queries working for both Level 1 and Level 3

### 📊 **CURRENT DATA STATUS**
- **Total Records**: 393 (Level 1: 145 + Level 3: 248)
- **Price Levels**: 2/5 implemented (Producer + Consumer)
- **Commodities**: 35 total (13 producer + 22 consumer)
- **Coverage**: 88% of core commodities (22/25 essential items)
- **Province**: NATIONAL only (Indonesia-wide aggregate)

## Decisions (proposed defaults)
- Province scope: **FOCUS ON NATIONAL LEVEL ONLY** using `province_id='NATIONAL'`. Single province for comprehensive Indonesian market analysis.
- Level harga scope: **PHASED EXPANSION** - ✅ Level 1 (Producer) completed, 🔄 Level 2 (Wholesale) next, then Level 4/5 (Export/Import).
- **PRIORITY**: Implement multi-level data ingestion for complete market coverage (producer → wholesale → consumer → export/import).
- **HISTORICAL DATA**: Add 2023 and earlier data for trend analysis and forecasting.
- Units: store verbatim; do not cross-aggregate different units.
- IDs: store `commodity_id` as text to keep schema flexible; convert to integer in views if needed.
- Validation: fail fast on unknown month keys; log payload sample. Skip null/absent months without creating rows.
- Timeouts/backoff: httpx total timeout 20s; backoff 1,2,4,8,16s; max 5 attempts per window.
- Scheduling: **Weekly level rotation** (cycle through all 5 price levels); **Monthly historical updates** (add previous year data); Mirror schedules in OS cron.

## API Examples (current & future)

### ✅ **WORKING NOW**
- **Consumer prices**: `GET /prices?level_harga_id=3&commodity_id=27&limit=5`
- **Producer prices**: `GET /prices?level_harga_id=1&commodity_id=2&limit=5`
- **List all commodities**: `GET /commodities` (35 total available)
- **List provinces**: `GET /provinces` (NATIONAL aggregate)

### 🔄 **PHASE 4A (In Progress)**
- **Wholesale prices** (next): `GET /prices?level_harga_id=2&commodity_id=X`
- **Export prices**: `GET /prices?level_harga_id=4&commodity_id=X`
- **Import prices**: `GET /prices?level_harga_id=5&commodity_id=X`

### 🚀 **PHASE 4B (Future)**
- **Historical trends**: `GET /prices?level_harga_id=3&period_start=2023-01-01&period_end=2024-12-31`
- **Cross-level comparisons**: Producer vs Consumer price analysis

## Backfill & Seed Strategy
- Initial seed: backfill last 3 months (rolling) at boot or via one-shot CLI.
- On-demand: admin endpoint/CLI `fetch_and_upsert(start_year,end_year,period_start,period_end,level_harga_id,province_id?)`.
- Drift control: monthly rebuild for the previous full month to capture late upstream corrections.

## First Scrape Verification (Pre-DB)

Goal: prove upstream availability and schema expectations before DB work.

- Success criteria:
  - HTTP 200 and JSON object payload
  - Has `request_data` and `data` keys; year buckets under `data` (e.g., `{"2024": [...]}`)
  - At least one commodity record returned for a recent window and `level_harga_id=3`
  - `today_province_price.satuan` present (unit)
  - Month keys subset of `{Jan,Feb,Mar,Apr,Mei,Jun,Jul,Agu,Sep,Okt,Nov,Des}`

- Curl smoke test (national aggregate):
  - curl 'https://api-panelhargav2.badanpangan.go.id/api/front/harga-pangan-bulanan-v2?start_year=2024&end_year=2025&period_date=01%2F11%2F2024%20-%2030%2F11%2F2024&province_id=&level_harga_id=3' -H 'Accept: application/json' -H 'Origin: https://panelharga.badanpangan.go.id' -H 'Referer: https://panelharga.badanpangan.go.id/'

- Programmatic smoke test (no DB):
  - python3 - <<'PY'
    from datetime import date
    from app.infra.http.upstream import make_upstream_client
    from app.usecases.ports import FetchParams
    MONTH_KEYS = {"Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"}
    client = make_upstream_client()
    params = FetchParams(start_year=2024, end_year=2025, period_start=date(2024,11,1), period_end=date(2024,11,30), level_harga_id=3)
    data = client.fetch(params)
    assert isinstance(data, dict) and 'data' in data and 'request_data' in data
    buckets = data['data']
    total_records = 0
    sample = None
    for year, arr in buckets.items():
        if isinstance(arr, list):
            total_records += len(arr)
            sample = sample or (arr[0] if arr else None)
    assert total_records > 0, 'No commodity records returned'
    if sample:
        months = {k for k in sample.keys() if k in MONTH_KEYS}
        unknown = {k for k in sample.keys() if k.isalpha() and k not in MONTH_KEYS and len(k) <= 3}
        assert not unknown, f'Unknown month keys: {unknown}'
        unit = (sample.get('today_province_price') or {}).get('satuan')
        assert unit, 'Missing unit (satuan)'
    print({'ok': True, 'records': total_records})
    PY

- Optional: add `scripts/dev.py scrape-test [--save payload.json]` to run the above and optionally persist the payload for offline debugging.

## Scrape → Normalize → Save (DB)

Objective: transform a verified upstream payload into normalized monthly rows and persist idempotently.

Pipeline:
- Fetch using `make_upstream_client()` with `FetchParams`.
- Normalize to `PriceUpsertRow[]`:
  - For each commodity record in year buckets, iterate month keys `Jan..Des`.
  - Skip null/absent month values.
  - Compute `period_start`/`period_end` for the month in Asia/Jakarta calendar.
  - Set `province_id='NATIONAL'` unless ingesting for a specific province.
  - Derive `unit` from `today_province_price.satuan`.
  - Compute `checksum` using `compute_price_checksum(...)`.
- Upsert via `PriceRepositoryPort.upsert_many` using a SQLAlchemy `Engine`.
- Verify summary: `inserted + updated + unchanged == len(rows)`; log counts.

Notes:
- Unique window key `(commodity_id, province_id, level_harga_id, period_start, period_end)` guarantees idempotency.
- `checksum` drives update-vs-unchanged decision without changing the unique key.

DB Smoke Test (one-shot ingest):
- python3 - <<'PY'
  from datetime import date
  from app.infra.http.upstream import make_upstream_client
  from app.usecases.ports import FetchParams, PriceUpsertRow
  from app.common.checksum import compute_price_checksum
  from app.infra.db import get_engine
  from app.infra.repositories.prices import make_price_repository

  MONTHS = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"Mei":5,"Jun":6,"Jul":7,"Agu":8,"Sep":9,"Okt":10,"Nov":11,"Des":12}

  def month_edges(year:int, month:int):
      from calendar import monthrange
      start = date(year, month, 1)
      end = date(year, month, monthrange(year, month)[1])
      return start, end

  params = FetchParams(start_year=2024, end_year=2025, period_start=date(2024,11,1), period_end=date(2024,11,30), level_harga_id=3)
  client = make_upstream_client()
  payload = client.fetch(params)
  buckets = payload.get('data') or {}

  rows: list[PriceUpsertRow] = []
  for year_str, items in buckets.items():
      try:
          yr = int(year_str)
      except Exception:
          continue
      if not isinstance(items, list):
          continue
      for it in items:
          unit = ((it or {}).get('today_province_price') or {}).get('satuan') or ''
          commodity_id = str(it.get('Komoditas_id')) if it and 'Komoditas_id' in it else None
          if not commodity_id:
              continue
          for mk, mnum in MONTHS.items():
              if mk not in it or it[mk] in (None, ""):
                  continue
              price_val = it[mk]
              ps, pe = month_edges(yr, mnum)
              row = PriceUpsertRow(
                  commodity_id=commodity_id,
                  province_id='NATIONAL',
                  level_harga_id=params.level_harga_id,
                  period_start=ps,
                  period_end=pe,
                  price=price_val,
                  unit=unit,
                  checksum=compute_price_checksum(
                      price=price_val,
                      unit=unit,
                      level_harga_id=params.level_harga_id,
                      period_start=ps,
                      period_end=pe,
                      commodity_id=commodity_id,
                  ),
              )
              rows.append(row)

  engine = get_engine()
  repo = make_price_repository(engine=engine)
  summary = repo.upsert_many(rows)
  print({
      'rows': len(rows),
      'inserted': summary.inserted,
      'updated': summary.updated,
      'unchanged': summary.unchanged,
  })
  PY

Success criteria:
- Script prints non-zero `rows`, and either `inserted` or `unchanged` is non-zero.
- Re-running should move counts from `inserted` to `unchanged` unless upstream changed (then `updated` increases).
 - Equivalent via CLI: `python scripts/dev.py ingest --dry-run` (no writes) and `python scripts/dev.py ingest` (persist) using the same window.

## Compliance Mode
- If required to avoid redistributing raw data, add a toggle to serve only aggregates:
  - Monthly mean/median per `(commodity, province|NATIONAL, level_harga_id)`
  - Percentage deltas (MoM/YoY) computed from cached facts
  - Keep raw facts internal; document clearly in API docs
