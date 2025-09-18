i want create API scrapping for get data from API:

curl 'https://api-panelhargav2.badanpangan.go.id/api/front/harga-pangan-bulanan-v2?start_year=2023&end_year=2025&period_date=07%2F11%2F2024%20-%2030%2F11%2F2024&province_id=&level_harga_id=3' \
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

save into database since origin so slow

so i get data from that, save my DB and than can use it for people.

---

## **DATA EXPANSION STRATEGY DISCUSSION & DECISIONS (2025-09-18)**

### **Problem Identified**
User tried realistic API query but got empty results:
```bash
curl 'http://localhost:8000/prices?level_harga_id=1&commodity_id=3&province_id=10&period_start=2024-11-01&period_end=2024-12-30'
# Result: {"data": [], "total": 0}
```

**Root Cause Analysis:**
- `commodity_id=3` doesn't exist (our data uses IDs like "27", "28", "30")
- `province_id=10` doesn't exist (we only have "NATIONAL")
- `level_harga_id=1` not ingested (we only have level 3)

### **Current Data Coverage (Phase 3 Complete)**
- ✅ **25 commodities** (100% coverage)
- ❌ **1 province** (NATIONAL only - 2.6% of Indonesia)
- ❌ **1 level_harga_id** (level 3 only - 20% coverage)
- ✅ **12 months** (2024 complete)
- **Total**: 25 × 1 × 1 × 12 = **248 records**

### **API Source Capabilities (Confirmed)**
✅ **Multi-Province Support**: ACEH, SUMUT, JABAR, JATENG, JATIM, DKI, etc. (BUT WE KEEP NATIONAL ONLY)
✅ **Multi-Level Support**: Level 1 (Producer), 2 (Wholesale), 3 (Consumer), 4 (Export), 5 (Import)
✅ **Historical Data**: 2023, 2022, and earlier years available

### **CORRECTED Phase 4 Strategy: Level Expansion Only**

#### **Phase 4A: Price Level Expansion (Weeks 1-4)**
1. **Level Expansion** (Week 1): Add levels 1, 2, 4, 5 to NATIONAL province
   - **Impact**: 25 commodities × 1 province × 5 levels × 12 months = **1,500 records**
2. **Historical Data** (Week 2): Add 2023 data for all levels
   - **Impact**: 25 commodities × 1 province × 5 levels × 24 months = **3,000 records**
3. **Level Rotation Scheduling** (Week 3): Automated level updates
4. **Data Optimization** (Week 4): Performance and completeness improvements

#### **Phase 4B: Intelligent Scheduling (Weeks 5-8)**
1. **Level Rotation**: Weekly cycle through price levels
2. **Historical Backfill**: Monthly add previous years
3. **Smart Refresh**: Weekly updates for recent data only
4. **APScheduler Implementation**: Automated background jobs

### **Key Decisions Made**

#### **Q: How far back should we go for historical data?**
**Decision**: Start with 2024 (current), then 2023, then earlier
**Reasoning**: Recent data more valuable, API may have limits

#### **Q: Get ALL 38 provinces immediately?**
**Decision**: No, start with 4 major provinces
**Reasoning**: Manageable data volume, focus on high-value areas

#### **Q: Which level_harga_id values first?**
**Decision**: Consumer (3) → Producer (1) → Wholesale (2) → Others (4,5)
**Reasoning**: Consumer data most relevant for public API

#### **Q: How to handle province/level matrix efficiently?**
**Decision**: Implement rotation scheduling
**Reasoning**: Avoid API overload, ensure steady growth

### **CORRECTED Expected Growth Trajectory**
```
Current (Phase 3):       25 × 1 × 1 × 12 =   248 records
After Level Expansion:   25 × 1 × 5 × 12 = 1,500 records (+1,252)
With Historical Data:    25 × 1 × 5 × 24 = 3,000 records (+1,500)
Future Potential:        25 × 1 × 5 × 60 = 7,500 records (if we go back 5 years)
```

**Growth**: **6x increase** (manageable, focused on quality over quantity)

### **Technical Implementation Plan**

1. **Level Mapping Creation** (1=Producer, 2=Wholesale, 3=Consumer, 4=Export, 5=Import)
2. **Enhanced Ingestion Scripts** (multi-level support)
3. **Database Optimization** (efficient storage/querying)
4. **API Endpoint Updates** (reflect new price level availability)
5. **Monitoring Dashboard** (track data completeness by level)

### **Success Metrics for Phase 4A**
- [ ] API queries return meaningful data for all price levels (1-5)
- [ ] Users can compare producer vs consumer prices
- [ ] Historical trends possible (2023-2024 comparison)
- [ ] Performance maintained with 6x data growth

### **IMMEDIATE NEXT STEPS (Phase 4A Implementation)**
1. **Week 1**: Add level_harga_id=1 (Producer) data
   - Command: `python scripts/dev.py ingest --start 2024-01 --end 2024-12 --level 1 --province NATIONAL`
   - Expected: 25 commodities × 12 months = 300 records added
2. **Week 2**: Add level_harga_id=2 (Wholesale) data
   - Command: `python scripts/dev.py ingest --start 2024-01 --end 2024-12 --level 2 --province NATIONAL`
   - Expected: 25 commodities × 12 months = 300 records added
3. **Week 3**: Add level_harga_id=4 & 5 (Export/Import) data
   - Commands: Separate runs for level 4 and 5
   - Expected: 25 commodities × 12 months × 2 levels = 600 records added
4. **Week 4**: Add 2023 historical data for all levels
   - Commands: Run ingestion for each level with `--start 2023-01 --end 2023-12`
   - Expected: 25 commodities × 12 months × 5 levels = 1,500 records added

### **IMPLEMENTATION STATUS**
- ✅ **Current Data**: 25 commodities × 1 NATIONAL × 1 level (3) × 12 months = **248 records**
- 🔄 **Phase 4A Goal**: 25 commodities × 1 NATIONAL × 5 levels × 12 months = **1,500 records**
- 🎯 **Final Goal**: 25 commodities × 1 NATIONAL × 5 levels × 24 months = **3,000 records** (2023-2024)

### **Why This CORRECTED Strategy Makes Sense**
- **Focused Growth**: 6x increase manageable and targeted
- **Quality over Quantity**: Deep data (5 price levels) vs wide coverage
- **API-Friendly**: Level rotation prevents overwhelming upstream service
- **User-Centric**: NATIONAL aggregate covers Indonesia-wide analysis
- **Maintainable**: Single province focus reduces complexity

### **API CAPABILITIES AFTER COMPLETION**

**Before Phase 4A:**
```bash
# Works: Consumer prices only
curl "http://localhost:8000/prices?level_harga_id=3&commodity_id=27"
# Returns: Consumer prices for Beras Premium

# Doesn't work: Other price levels
curl "http://localhost:8000/prices?level_harga_id=1&commodity_id=27"
# Returns: {"data": [], "total": 0}
```

**After Phase 4A:**
```bash
# All price levels available
curl "http://localhost:8000/prices?level_harga_id=1&commodity_id=27"  # Producer prices
curl "http://localhost:8000/prices?level_harga_id=2&commodity_id=27"  # Wholesale prices
curl "http://localhost:8000/prices?level_harga_id=3&commodity_id=27"  # Consumer prices
curl "http://localhost:8000/prices?level_harga_id=4&commodity_id=27"  # Export prices
curl "http://localhost:8000/prices?level_harga_id=5&commodity_id=27"  # Import prices

# Price comparison queries
curl "http://localhost:8000/prices?commodity_id=27&period_start=2024-01-01&period_end=2024-12-31"
# Returns: All 5 price levels for 2024, enabling price margin analysis
```

**Value Added:**
- **Market Analysis**: Compare producer vs consumer price margins
- **Supply Chain**: Track wholesale price movements
- **Trade Analysis**: Monitor export/import price differentials
- **Trend Analysis**: Historical data for forecasting
- **Complete Market View**: All price levels in Indonesian food market 

this help me learn
- scrap data from that API
- save database
- crop job for each week / month
- docs on API

# Pendekatan A — Python (FastAPI + PostgreSQL + APScheduler)

## Tasklist (urut eksekusi)

1. Init repo + struktur
2. Jalankan Postgres + API (Docker)
3. Seed pertama (1–3 bulan terakhir)
4. Jadwalkan job mingguan & bulanan
5. Ekspos API publik + docs
6. Healthcheck, retry, idempotensi
7. Observabilitas (log + audit)

## Commands

```bash
# 1) Init
git init pangan-cache && cd pangan-cache
mkdir -p app
printf 'postgres:\n  image: postgres:16\n  environment:\n    POSTGRES_PASSWORD: dev\n    POSTGRES_DB: pangan\n  ports: ["5432:5432"]\napi:\n  build: .\n  environment:\n    DATABASE_URL: postgresql+psycopg://postgres:dev@postgres:5432/pangan\n    TZ: Asia/Jakarta\n  ports: ["8080:8080"]\n  depends_on: [postgres]\n' > compose.yml

# 2) Dockerfile (ringkas)
cat > Dockerfile <<'EOF'
FROM python:3.12-slim
WORKDIR /app
RUN pip install fastapi uvicorn[standard] SQLAlchemy psycopg[binary] requests apscheduler
COPY app /app/app
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]
EOF

# 3) Tambahkan kode app/main.py (pakai versi yang sudah saya berikan tadi)
#    -> simpan persis sebagai app/main.py

# 4) Up services
docker compose -f compose.yml up -d --build
docker compose ps
docker compose logs -f api | sed -n '1,120p'

# 5) Cek docs API
# open http://localhost:8080/docs

# 6) Seed pertama (contoh: tarik 3 bulan terakhir)
#    Opsi cepat: panggil fungsi dari dalam kontainer sekali
docker compose exec api python - <<'PY'
import datetime as dt
from app.main import fetch_and_upsert
today=dt.date.today()
for i in range(0,3):
    first=dt.date(today.year, today.month, 1) - dt.timedelta(days=1)
    first=dt.date(first.year, first.month, 1) - dt.timedelta(days=0)
    first=dt.date(today.year, today.month-i, 1)
    last=(dt.date(first.year + (first.month==12), 1 if first.month==12 else first.month+1, 1)-dt.timedelta(days=1))
    fetch_and_upsert(first.year, last.year, first, last, 3, None)
print("seed done")
PY

# 7) Query data dari cache (contoh)
curl 'http://localhost:8080/prices?level_harga_id=3&period_start=2024-11-01&period_end=2024-11-30&limit=10' | jq .

# 8) Jadwalkan cron OS untuk keandalan (hindari APScheduler-only)
#    Weekly refresh: Senin 01:00 WIB
(crontab -l 2>/dev/null; echo '0 1 * * 1 docker compose -f /path/ke/compose.yml exec -T api python - <<PY
import datetime as dt
from app.main import fetch_and_upsert
today=dt.date.today()
first=dt.date(today.year,today.month,1)
last=(dt.date(first.year + (first.month==12), 1 if first.month==12 else first.month+1, 1)-dt.timedelta(days=1))
fetch_and_upsert(first.year,last.year,first,last,3,None)
PY') | crontab -

#    Monthly rebuild: tanggal 1 02:00 WIB (late updates)
(crontab -l 2>/dev/null; echo '0 2 1 * * docker compose -f /path/ke/compose.yml exec -T api python - <<PY
import datetime as dt
from app.main import fetch_and_upsert
today=dt.date.today()
prev_first=(dt.date(today.year,today.month,1)-dt.timedelta(days=1)).replace(day=1)
prev_last=(dt.date(prev_first.year + (prev_first.month==12), 1 if prev_first.month==12 else prev_first.month+1, 1)-dt.timedelta(days=1))
fetch_and_upsert(prev_first.year,prev_last.year,prev_first,prev_last,3,None)
PY') | crontab -
```

## Kontrak API (ringkas)

```
GET /prices?commodity_id&province_id&level_harga_id=3&period_start=YYYY-MM-DD&period_end=YYYY-MM-DD&limit
# 📒 OpenAPI otomatis di /docs
```

## Catatan kritis

* Kelemahan: APScheduler in-process rawan mati saat container restart; mitigasi dengan cron OS seperti di atas.
* Validasi shape JSON sumber: tambahkan try/except + schema check bila API berubah.
* Legal: cek ToS; kalau raw dilarang, simpan agregat (median/mean, delta %).

—

# Pendekatan B — TypeScript (Bun/Hono + Prisma + BullMQ + Redis)

## Tasklist (urut eksekusi)

1. Init repo + env
2. Postgres + Redis + API + Worker (Docker)
3. Prisma migrate + seed 3 bulan
4. Jadwal repeat job BullMQ (weekly & monthly)
5. Ekspos API + Swagger (zod-openapi)
6. Healthcheck + retry + idempotensi

## Commands

```bash
# 1) Init
git init pangan-cache-ts && cd pangan-cache-ts
bun init -y
bun add hono @hono/zod-openapi @hono/swagger-ui zod undici @prisma/client prisma bullmq ioredis
bun add -d typescript tsx @types/node

# 2) Prisma schema
mkdir -p prisma src
# -> tempel file schema.prisma yang sudah saya beri (Commodity/Province/Price + unique)

# 3) .env
cat > .env <<'EOF'
DATABASE_URL="postgresql://postgres:dev@postgres:5432/pangan"
REDIS_URL="redis://redis:6379"
PORT=8787
TZ=Asia/Jakarta
EOF

# 4) Docker compose
cat > compose.yml <<'YML'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: dev
      POSTGRES_DB: pangan
    ports: ["5432:5432"]
  redis:
    image: redis:7
    ports: ["6379:6379"]
  api:
    build: .
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      PORT: 8787
    ports: ["8787:8787"]
    depends_on: [postgres, redis]
  worker:
    build: .
    command: ["bun","run","src/worker.ts"]
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
    depends_on: [postgres, redis]
YML

# 5) Dockerfile
cat > Dockerfile <<'EOF'
FROM oven/bun:1
WORKDIR /app
COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile
COPY . .
CMD ["bun","run","src/server.ts"]
EOF

# 6) Tambahkan file:
#   - src/fetcher.ts  (ingestMonth)  -> pakai versi yang saya beri
#   - src/server.ts   (route /prices + /docs) -> versi yang saya beri
#   - src/worker.ts   (Queue + repeat weekly) -> versi yang saya beri

# 7) Migrate
bunx prisma generate
bunx prisma migrate dev --name init

# 8) Up
docker compose up -d --build
docker compose logs -f api | sed -n '1,120p'

# 9) Seed 3 bulan terakhir (enqueue)
docker compose exec api bun run - <<'JS'
import { Queue } from "bullmq"
import IORedis from "ioredis"
const q = new Queue("pangan-ingest",{ connection: new IORedis(process.env.REDIS_URL||"redis://redis:6379") })
function monthEdges(d){ const s=new Date(d.getFullYear(),d.getMonth(),1); const e=new Date(d.getFullYear(),d.getMonth()+1,0); return {s,e}}
const now=new Date()
for (let i=0;i<3;i++){ const m=new Date(now.getFullYear(), now.getMonth()-i, 1); const {s,e}=monthEdges(m); await q.add("month",{start:s.toISOString(),end:e.toISOString()}) }
console.log("seed enqueued")
process.exit(0)
JS

# 10) Jadwal repeat jobs (mingguan, Senin 01:00 WIB) sudah ada di worker.ts
#     Tambah monthly rebuild via repeat rule kedua:
docker compose exec api bun run - <<'JS'
import { Queue } from "bullmq"
import IORedis from "ioredis"
const q = new Queue("pangan-ingest",{ connection: new IORedis(process.env.REDIS_URL||"redis://redis:6379") })
await q.add("monthly-rebuild", {}, { repeat: { pattern: "0 2 1 * *", tz: "Asia/Jakarta" }})
console.log("monthly repeat set")
process.exit(0)
JS

# 11) Cek API
curl 'http://localhost:8787/prices?level_harga_id=3&from=2024-11-01&to=2024-11-30&limit=10' | jq .
# Docs: http://localhost:8787/docs
```

## Catatan kritis

* Kelemahan: butuh Redis (tambahan infra), perlu monitor antrean.
* Kekuatan: job durable; aman dari restart; repeat & retry dikelola BullMQ.
* Pastikan validasi shape JSON; jika kunci berubah (komoditas\_id, provinsi\_id, harga), fail fast + alert.

—

# “Crop” job mingguan/bulanan (kedua pendekatan)

* Mingguan (refresh bulan berjalan): `Senin 01:00 Asia/Jakarta`
* Bulanan (rebuild bulan lalu): `Tanggal 1 02:00 Asia/Jakarta`
* 📒 Alasan: data panel pemerintah sering late update; rebuild mencegah “drift”.

# Skema DB (keduanya sama)

```sql
-- 📒 Kunci unik untuk idempoten
UNIQUE (commodity_id, province_id, level_harga_id, period_start, period_end)
-- 📒 Dimensi terpisah agar tidak duplikasi nama
commodities(id text PK, name text)
provinces(id text PK, name text)
prices_monthly(… price numeric, unit text, checksum text, inserted_at, updated_at)
```

# Health & Operasional

* Liveness: query dummy `SELECT 1` Postgres; `GET /prices?limit=1`
* Alert: jika error 4xx/5xx dari sumber berturut-turut > N, kirim log/Slack
* Backoff: exponential 1,2,4,8,16 s (sudah di kode contoh)
* Caching: simpan hasil terakhir per (komoditas, provinsi, bulan) → hindari hit berulang

# Risiko & mitigasi (cek sebelum live)

* Perubahan format sumber → tambahkan schema guard, contoh Zod/Pydantic, reject & log contoh payload.
* Batasan legal/ToS → jika tak boleh redistribusi raw, hanya serve agregat (mean/median, yoy, mom).
* Unit tidak konsisten → simpan `unit` di row; jangan gabungkan komoditas lintas unit.

# Keputusan cepat

* Butuh “jalan cepat, infra minim” → A.
* Butuh “durable queue + aman restart” → B.

---

## Design Decision: Ports Style (Protocol vs Functional)

Context
- AGENTS.md prefers a functional, declarative style and to avoid classes where possible.
- Phase 2 introduces “ports” to decouple use cases from infra (HTTP client and repositories).
- Current `app/usecases/ports.py` uses dataclasses for DTOs and `typing.Protocol` for interfaces.

Options
1) Protocol interfaces (current)
   - Example: `class PriceRepositoryPort(Protocol): def upsert_many(...): ...; def query(...): ...`
2) Callable type aliases
   - Example: `UpstreamFetchFn = Callable[[FetchParams], Mapping]`, `UpsertManyFn = Callable[...]`
3) Functional records (dataclass of callables; RORO-friendly)
   - Example:
     ```python
     @dataclass(frozen=True)
     class PriceRepositoryPort:
         upsert_many: UpsertManyFn
         query: QueryPricesFn
     ```

Pros & Cons
- Protocol interfaces
  - Pros: rich static typing across multi-method ports; cohesive grouping; good IDE autocomplete; easy duck-typed fakes.
  - Cons: introduces class constructs; nudges towards class-based adapters; more boilerplate; less aligned with AGENTS.md.
- Callable type aliases
  - Pros: purely functional; minimal boilerplate; trivial to mock and compose.
  - Cons: for multi-op ports (e.g., repository upsert+query) you pass multiple callables, reducing cohesion and discoverability.
- Functional records (dataclass of callables)
  - Pros: functional (no methods/state), cohesive grouping, clear DI (receive one object), strong typing via callables, matches RORO.
  - Cons: slightly more setup than bare callables; still uses a dataclass (a class construct) but without methods/OO semantics.

Recommendation
- Use Functional Records for ports in Phase 2.
  - Keep DTOs as `@dataclass` value objects (no behavior).
  - Rationale: best balance of AGENTS.md guidance and maintainability; avoids OO services while keeping ports cohesive and strongly typed.

Adapter shape (functional)
- HTTP client adapter returns an `UpstreamClientPort(fetch=...)` closing over config/session.
- Repository adapters return a `PriceRepositoryPort(upsert_many=..., query=...)` closing over a Session factory/engine.

Migration (from Protocol)
1) Introduce callable aliases and functional records in `ports.py` alongside Protocols.
2) Update use cases to accept functional records.
3) Replace Protocols once all call sites are migrated.
4) Keep DTOs unchanged.

Impact
- Aligns with AGENTS.md (functional, declarative).
- Strong typing and DI ergonomics preserved.
- Low refactor cost and reduces future friction.

Decision
- Proceed with functional records for ports before wiring Phase 2 adapters.
