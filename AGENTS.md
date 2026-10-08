# Repository Directives & Guidelines

## Core Principles

### 1. Mandatory GitHub Actions Verification (Absolute Rule)
> [!IMPORTANT]
> **WHEN PUSHING ANY CHANGE, THE GITHUB ACTION MUST BE CHECKED AND PASS.**
> - Whenever code is pushed to this repository (`git push`), you MUST monitor and verify the triggered GitHub Action workflow runs (`gh run list`, `gh run watch`).
> - Every job (Backend Tests, Frontend Tests, Lint, Build) must pass before a task is considered complete.
> - If an Action fails, diagnose immediately via `gh run view <id> --log-failed`, resolve all issues, push fixes, and verify that the re-run passes.
> - Never assume a push succeeded without actively inspecting GitHub Actions status.

### 2. Zero-Downtime & High-Throughput Ingestion
- Maintain strict rate limits ($\le 10\text{ req/s}$) across all Wargaming API clients.
- All telemetry and scraper processes must report live heartbeats to PostgreSQL `pipeline_state`.
- Big numeric combat fields (damage, XP, battery shots) must use `BigInteger` (`bigint`) to avoid 32-bit integer overflow.
- All high-frequency queries and database updates must use index range scans or table metadata (`pg_class.reltuples`) to preserve database IOPS and buffer cache.
