#!/usr/bin/env python3
"""
Development utilities script.
Run quality gates and development tasks.
"""

import subprocess
import sys
import os
from pathlib import Path
import json
from typing import Any

# Add project root to Python path so we can import app modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def _load_json_file(path: str | None) -> list[dict[str, Any]] | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        print(f"⚠️  File not found: {path}")
        return None
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data  # expect list of {id,name}
        print("⚠️  JSON must be an array of objects: {id,name}")
        return None
    except Exception as e:
        print(f"❌ Failed to read JSON {path}: {e}")
        return None


def run_command(cmd: list[str], cwd: Path = None) -> bool:
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def lint_check():
    """Run ruff linting checks."""
    print("🔍 Running lint checks...")
    return run_command(["ruff", "check", "app/"])


def format_code():
    """Format code with ruff."""
    print("🎨 Formatting code...")
    return run_command(["ruff", "format", "app/"])


def type_check():
    """Run type checking with mypy (when available)."""
    print("🔍 Running type checks...")
    # For now, just print that mypy is not configured yet
    print("ℹ️  Type checking will be available after mypy setup")
    return True


def quality_gates():
    """Run all quality gates."""
    print("🚀 Running all quality gates...")

    success = True

    if not lint_check():
        success = False

    if not format_code():
        success = False

    if not type_check():
        success = False

    if success:
        print("✅ All quality gates passed!")
    else:
        print("❌ Some quality gates failed!")
        sys.exit(1)


def run_dev():
    """Run development server."""
    print("🚀 Starting development server...")
    run_command(["uvicorn", "app.main:app", "--reload", "--port", "8000"])


def seed_dimensions_cmd(args: list[str]) -> None:
    """Seed static dimensions: commodities and provinces.

    Usage:
      python scripts/dev.py seed-dimensions [commodities.json] [provinces.json]

    Each JSON file should be an array of objects: [{"id": "...", "name": "..."}]
    If files are omitted, provinces will seed with a minimal default (NATIONAL),
    and commodities will be skipped.
    """
    from sqlalchemy.orm import Session
    from app.infra.db import get_engine
    from app.infra.seeding import seed_dimensions

    commodities = _load_json_file(args[0]) if len(args) >= 1 else None
    provinces = _load_json_file(args[1]) if len(args) >= 2 else None

    # Create session and run seeding
    engine = get_engine()
    with Session(bind=engine, future=True) as db:
        summary = seed_dimensions(db, commodities=commodities, provinces=provinces)
    print(
        "✅ Seeding completed:",
        f"commodities upserted={summary['commodities']}",
        f"provinces upserted={summary['provinces']}",
    )


def _prev_month_edges(today=None):
    import datetime as dt
    if today is None:
        today = dt.date.today()
    first_this = dt.date(today.year, today.month, 1)
    last_prev = first_this - dt.timedelta(days=1)
    first_prev = dt.date(last_prev.year, last_prev.month, 1)
    return first_prev, last_prev


def scrape_test_cmd(args: list[str]) -> None:
    """Scrape Verification (Pre-DB): fetch upstream and validate shape.

    Usage:
      python scripts/dev.py scrape-test [--level 3] [--year YYYY --month MM] [--province NATIONAL] [--save payload.json] [--mock]

    Options:
        --mock: use mock data instead of real upstream API (useful when upstream is down)

    Defaults: January 2025, level=3, province=NATIONAL (empty province_id to upstream)
    """
    import argparse
    import json
    from datetime import date
    from pathlib import Path

    from app.infra.http.upstream import make_upstream_client
    from app.usecases.ports import FetchParams

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--level", type=int, default=3)
    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--province", type=str, default="NATIONAL")
    parser.add_argument("--save", type=str)
    parser.add_argument("--mock", action="store_true", help="Use mock data for development/testing")
    ns, _ = parser.parse_known_args(args)

    MONTH_KEYS = {"Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"}

    if ns.year and not ns.month or ns.month and not ns.year:
        print("❌ Provide both --year and --month, or neither to use January 2025.")
        sys.exit(1)

    if ns.year and ns.month:
        from calendar import monthrange
        try:
            ps = date(ns.year, ns.month, 1)
            pe = date(ns.year, ns.month, monthrange(ns.year, ns.month)[1])
        except Exception as e:
            print(f"❌ Invalid year/month: {e}")
            sys.exit(1)
    else:
        # Default to January 2025 (known to work reliably)
        ps = date(2025, 1, 1)
        pe = date(2025, 1, 31)

    params = FetchParams(
        start_year=ps.year,
        end_year=pe.year,
        period_start=ps,
        period_end=pe,
        level_harga_id=ns.level,
        province_id=None if ns.province == "NATIONAL" else ns.province,
    )

    client = make_upstream_client(use_mock=ns.mock)

    # Test connection first (skip for mock)
    if not ns.mock:
        print("🔍 Testing upstream connectivity...")
        try:
            if not client.test_connection():
                print("❌ Upstream endpoint is not accessible.")
                print("💡 Suggestions:")
                print("   - Check your internet connection")
                print("   - The upstream API might be temporarily down")
                print("   - Try again in a few minutes")
                print("   - Use --mock flag for development testing")
                sys.exit(1)
            print("✅ Upstream endpoint is accessible")
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            print("💡 Try using --mock flag for development testing")
            sys.exit(1)
    else:
        print("🎭 Using mock mode - skipping connectivity test")

    try:
        data = client.fetch(params)
    except ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("💡 The upstream API may be experiencing issues.")
        print("💡 Try using --mock flag for development testing")
        sys.exit(2)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(2)

    if not isinstance(data, dict):
        print("❌ Unexpected payload: not a JSON object")
        sys.exit(3)

    if "data" not in data or "request_data" not in data:
        print("❌ Missing required keys: 'data' and/or 'request_data'")
        sys.exit(3)

    buckets = data.get("data") or {}
    total_records = 0
    sample = None
    for _year, arr in buckets.items():
        if isinstance(arr, list):
            total_records += len(arr)
            if arr and sample is None:
                sample = arr[0]

    if total_records <= 0:
        print("❌ No commodity records returned for the window")
        sys.exit(4)

    if sample:
        unknown = {k for k in sample.keys() if k.isalpha() and len(k) <= 3 and k not in MONTH_KEYS}
        if unknown:
            print(f"❌ Unknown month keys in sample: {sorted(unknown)}")
            sys.exit(5)
        unit = (sample.get("today_province_price") or {}).get("satuan")
        if not unit:
            print("❌ Missing unit (today_province_price.satuan) in sample commodity")
            sys.exit(6)

    if ns.save:
        try:
            p = Path(ns.save)
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"💾 Saved payload to {p}")
        except Exception as e:
            print(f"⚠️  Failed to save payload: {e}")

    print(json.dumps({
        "ok": True,
        "records": total_records,
        "period_start": ps.isoformat(),
        "period_end": pe.isoformat(),
        "level": ns.level,
        "province": ns.province,
    }))
    # Success
    return


def ingest_cmd(args: list[str]) -> None:
    """Ingest monthly data over a range (API supports one month per request).

    Usage:
      python scripts/dev.py ingest [--start YYYY-MM] [--end YYYY-MM] [--level 3] [--province NATIONAL] [--dry-run] [--save-dir DIR] [--mock]

    Defaults: start=2025-01, end=2025-07 (inclusive), level=3, province=NATIONAL.
    """
    import argparse
    from datetime import date
    from calendar import monthrange
    from pathlib import Path
    import json

    from sqlalchemy.orm import Session

    from app.common.logging import setup_logging
    from app.infra.http.upstream import make_upstream_client
    from app.infra.db import get_engine
    from app.infra.repositories.prices import make_price_repository
    from app.infra.seeding import seed_dimensions
    from app.usecases.ports import FetchParams
    from app.usecases.ingest import fetch_and_upsert, _normalize_payload, _with_checksums
    from app.usecases.schemas import UpstreamPayload

    # Setup structured logging
    setup_logging("INFO")

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--start", type=str, default="2025-01", help="Start month inclusive in YYYY-MM")
    parser.add_argument("--end", type=str, default="2025-07", help="End month inclusive in YYYY-MM")
    parser.add_argument("--level", type=int, default=3)
    parser.add_argument("--province", type=str, default="NATIONAL")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--save-dir", type=str)
    parser.add_argument("--save", type=str, help="Save final summary or combined rows to a single file")
    parser.add_argument("--mock", action="store_true")
    ns, _ = parser.parse_known_args(args)

    def parse_ym(s: str) -> tuple[int, int]:
        try:
            y, m = s.split("-")
            return int(y), int(m)
        except Exception as e:
            print(f"❌ Invalid year-month '{s}': {e}")
            sys.exit(1)

    sy, sm = parse_ym(ns.start)
    ey, em = parse_ym(ns.end)
    if (ey, em) < (sy, sm):
        print("❌ end must be >= start")
        sys.exit(1)

    client = make_upstream_client(use_mock=ns.mock)
    engine = get_engine()
    repo = make_price_repository(engine=engine)

    # Ensure NATIONAL province exists
    with Session(bind=engine, future=True) as db:
        seed_dimensions(db, provinces=None, commodities=None)

    total_rows = 0
    total_inserted = total_updated = total_unchanged = 0
    save_dir = Path(ns.save_dir) if ns.save_dir else None
    save_file = Path(ns.save) if ns.save else None
    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)

    y, m = sy, sm
    while (y, m) <= (ey, em):
        ps = date(y, m, 1)
        pe = date(y, m, monthrange(y, m)[1])
        params = FetchParams(
            start_year=ps.year,
            end_year=pe.year,
            period_start=ps,
            period_end=pe,
            level_harga_id=ns.level,
            province_id=None if ns.province == "NATIONAL" else ns.province,
        )

        print(f"📥 Ingesting {ps.isoformat()}..{pe.isoformat()} (level={ns.level}, province={ns.province})")
        payload = client.fetch(params)

        # Optionally save raw payload per month
        if save_dir:
            fname = save_dir / f"payload-{y:04d}-{m:02d}.json"
            try:
                fname.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as e:
                print(f"⚠️  Failed to save payload {fname}: {e}")

        # Seed commodities from payload (id + name)
        try:
            up = UpstreamPayload.model_validate(payload)
            commodities: dict[str, str] = {}
            for _ys, items in up.data.items():
                for it in items:
                    cid = str(it.commodity_id)
                    name = (it.name or cid).strip()
                    commodities[cid] = name
            if commodities:
                from sqlalchemy.orm import Session as _S
                with _S(bind=engine, future=True) as db:
                    seed_dimensions(
                        db,
                        commodities=[{"id": k, "name": v} for k, v in commodities.items()],
                        provinces=None,
                    )
        except Exception as e:
            print(f"⚠️  Failed to seed commodities from payload: {e}")

        # Normalize and (optionally) upsert
        import time
        import logging

        normalize_start = time.time()
        rows = _normalize_payload(payload=payload, params=params)
        normalize_duration = time.time() - normalize_start

        total_rows += len(rows)
        if ns.dry_run:
            print(f"🧪 Dry-run: {len(rows)} rows normalized for {y:04d}-{m:02d}")
            # Log dry-run operation
            logger = logging.getLogger(__name__)
            logger.info(
                "Dry-run ingestion completed",
                extra={
                    "operation": "ingest_dry_run",
                    "level_harga_id": params.level_harga_id,
                    "province_id": params.province_id or "NATIONAL",
                    "period_start": params.period_start.isoformat(),
                    "period_end": params.period_end.isoformat(),
                    "normalize_duration_ms": round(normalize_duration * 1000, 2),
                    "normalized_rows": len(rows),
                }
            )
        else:
            checksum_start = time.time()
            upsert_rows = _with_checksums(rows)
            checksum_duration = time.time() - checksum_start

            upsert_start = time.time()
            summary = repo.upsert_many(upsert_rows)
            upsert_duration = time.time() - upsert_start

            total_inserted += summary.inserted
            total_updated += summary.updated
            total_unchanged += summary.unchanged
            print(
                f"✅ Upserted: inserted={summary.inserted} updated={summary.updated} unchanged={summary.unchanged}"
            )

            # Structured logging for actual ingestion
            logger = logging.getLogger(__name__)
            logger.info(
                "Ingestion completed",
                extra={
                    "operation": "ingest",
                    "level_harga_id": params.level_harga_id,
                    "province_id": params.province_id or "NATIONAL",
                    "period_start": params.period_start.isoformat(),
                    "period_end": params.period_end.isoformat(),
                    "normalize_duration_ms": round(normalize_duration * 1000, 2),
                    "checksum_duration_ms": round(checksum_duration * 1000, 2),
                    "upsert_duration_ms": round(upsert_duration * 1000, 2),
                    "normalized_rows": len(rows),
                    "upsert_rows": len(upsert_rows),
                    "inserted": summary.inserted,
                    "updated": summary.updated,
                    "unchanged": summary.unchanged,
                }
            )

        # advance month
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1

    # Final summary
    final_summary = {
        "ok": True,
        "normalized_rows": total_rows,
        "inserted": total_inserted,
        "updated": total_updated,
        "unchanged": total_unchanged,
        "range": {"start": ns.start, "end": ns.end},
        "level": ns.level,
        "province": ns.province,
    }

    if save_file:
        try:
            save_file.write_text(json.dumps(final_summary, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"💾 Saved final summary to {save_file}")
        except Exception as e:
            print(f"⚠️  Failed to save final summary {save_file}: {e}")

    if ns.dry_run:
        print(
            json.dumps(
                {
                    "ok": True,
                    "normalized_rows": total_rows,
                    "range": {"start": ns.start, "end": ns.end},
                    "level": ns.level,
                    "province": ns.province,
                },
                ensure_ascii=False,
            )
        )
    else:
        # Pretty summary
        print("\n📊 Ingest summary")
        print(f"  Normalized rows: {total_rows}")
        print(f"  Inserted: {total_inserted}")
        print(f"  Updated: {total_updated}")
        print(f"  Unchanged: {total_unchanged}")
        print(f"  Range: {ns.start} → {ns.end}")
        # Fail if nothing was persisted (non-zero exit)
        persisted = total_inserted + total_updated + total_unchanged
        if persisted == 0:
            print("\n❌ No rows were persisted. Ingest failed or upstream returned no data.")
            sys.exit(2)
        # Also print machine-readable JSON
        print(json.dumps(final_summary, ensure_ascii=False))
    return

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/dev.py <command>")
        print("Commands:")
        print("  lint      - Run linting checks")
        print("  format    - Format code")
        print("  quality   - Run all quality gates")
        print("  dev       - Start development server")
        print("  seed-dimensions [commodities.json] [provinces.json] - Seed static dimensions")
        print("  scrape-test [--level 3] [--year YYYY --month MM] [--province NATIONAL] [--save payload.json] - Upstream scrape smoke test")
        print("  ingest [--start YYYY-MM] [--end YYYY-MM] [--level 3] [--province NATIONAL] [--dry-run] [--save-dir DIR] [--mock] - Ingest monthly data over a range")
        sys.exit(1)

    command = sys.argv[1]

    if command == "lint":
        success = lint_check()
    elif command == "format":
        success = format_code()
    elif command == "quality":
        quality_gates()
        return
    elif command == "dev":
        run_dev()
        return
    elif command == "seed-dimensions":
        seed_dimensions_cmd(sys.argv[2:])
        return
    elif command == "scrape-test":
        scrape_test_cmd(sys.argv[2:])
        return
    elif command == "ingest":
        ingest_cmd(sys.argv[2:])
        return
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
