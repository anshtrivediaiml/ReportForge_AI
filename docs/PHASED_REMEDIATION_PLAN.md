# Phased Remediation Plan

## Purpose

This document breaks the project work into phases so the codebase can move from its current prototype state to a production-grade report generator.

It covers:
- visible bugs
- structural issues
- production hardening work
- execution order

## Current Baseline

The repository is functionally ambitious but not yet production-ready.

Current known state:
- frontend build is stable again
- frontend/backend response contracts have been aligned for the initial high-risk routes
- processing/WebSocket flow is stabilized for current local and deployment-aware usage
- job deletion and storage accounting are now centralized around backend cleanup helpers
- repository contains generated artifacts, temp extracts, and noisy checked-in runtime output
- backend startup still uses `Base.metadata.create_all()`
- the report pipeline is advanced but still vulnerable to unsupported-input and isolation edge cases

## Goals

1. Restore a stable local development baseline.
2. Eliminate visible frontend and backend bugs.
3. Make contracts explicit and testable.
4. Harden the report pipeline for broader input coverage.
5. Replace prototype operational patterns with production-safe ones.
6. Add enough automated validation to prevent regressions.

## Phase 0 - Workspace Stabilization

### Objective

Make the repository clean enough to work on safely.

Status: Completed on 2026-03-08

### Tasks

- Add a proper root `.gitignore`.
- Stop tracking generated outputs where possible.
- Stop tracking temp extraction directories and local runtime artifacts.
- Review committed `node_modules`, database files, logs, and generated DOCX/JSON outputs.
- Define canonical source directories vs generated/runtime directories.

### Exit Criteria

- repository structure is clearly separated into source vs runtime output
- search results are not polluted by generated artifacts
- contributors can work without accidentally editing outputs

Completion notes:
- root `.gitignore` added
- root `.rgignore` added for cleaner source searches
- canonical source vs runtime boundaries documented
- repeatable runtime cleanup script added
- low-risk generated API output/temp directories cleaned successfully
- some top-level runtime directories remain physically present because OneDrive blocks removal of their container paths, but they are now explicitly classified as runtime-only and excluded from normal searches

## Phase 1 - Build and Type Safety Recovery

### Objective

Get the frontend back to a clean build and remove obvious compile-time issues.

Status: Completed on 2026-03-08

### Tasks

- Fix TypeScript build errors in `web/`
- add missing Vite env typings
- fix missing package type declarations such as `canvas-confetti`
- remove dead imports and unused variables
- fix nullable handling and strict typing errors
- standardize `import.meta.env` usage

### Exit Criteria

- `npm run build` passes
- no TypeScript errors remain in the frontend
- strict mode is preserved

Completion notes:
- added Vite env typing support
- added a local type declaration for `canvas-confetti`
- removed unused imports and unused state blocking strict mode
- fixed strict null handling in dashboard analytics rendering
- fixed frontend service typing issues needed for compilation
- validated `npx tsc --noEmit`
- validated `npm run build`
- bundle-size and chunking warnings remain as optimization follow-up items, not Phase 1 blockers

## Phase 2 - Frontend/Backend Contract Alignment

### Objective

Remove response-shape drift between API routes and frontend consumers.

Status: Completed on 2026-03-08

### Tasks

- inventory all API response contracts used by frontend pages and stores
- standardize wrapped vs unwrapped response shapes
- fix sharing contract mismatches
- fix analytics/job/auth contract assumptions
- reduce ad hoc `response.data.data || response.data` parsing
- centralize DTOs or generate typed client contracts

### Exit Criteria

- frontend services match backend response models
- share, job, analytics, auth, and download flows all use stable DTOs
- pages no longer depend on guessed response shapes

Completion notes:
- added a shared frontend API unwrapping utility for wrapped vs direct payload handling
- aligned auth, job, analytics, upload, and profile service parsing around explicit DTOs
- fixed the frontend register flow to accept the backend's direct `AuthResponse`
- fixed backend sharing response models to include `requires_password` and `description`
- updated processing and success pages to use normalized job responses directly
- removed stale frontend checks for a non-existent job status of `error`
- validated backend import sanity
- validated `npx tsc --noEmit`
- validated `npm run build`

## Phase 3 - Processing and Real-Time UX Fixes

### Objective

Make live job tracking reliable in both local and deployed environments.

Status: Completed on 2026-03-08

### Tasks

- replace hardcoded WebSocket URL construction with backend-provided URL or derived config
- stop duplicate progress/log application in processing flow
- distinguish intentional WebSocket disconnects from reconnect-worthy disconnects
- improve reconnect/backoff behavior
- ensure failed/completed job transitions are reflected exactly once
- fix timezone handling to use user-local time or UTC formatting

### Exit Criteria

- processing page works behind non-localhost deployments
- logs and progress are not duplicated
- reconnect behavior is predictable
- time displays are correct across environments

Completion notes:
- backend generation route now derives `ws_url` from the incoming request and forwarded headers instead of localhost-only defaults
- upload flow now preserves the backend-provided `ws_url` when navigating into processing
- processing page now resolves WebSocket URLs from navigation state, session storage, or API-base fallback
- removed duplicate progress/log application by dropping the overlapping generic message handler
- separated server error events from transport-level connection errors in the frontend WebSocket client
- intentional disconnects no longer trigger reconnect attempts
- reconnect attempts now emit explicit reconnecting/connection-error events
- log timestamps and shared date formatting now use the viewer's local locale instead of hardcoded `Asia/Kolkata`
- validated backend import sanity
- validated `npx tsc --noEmit`
- validated `npm run build`

## Phase 4 - File Lifecycle and Storage Integrity

### Objective

Ensure uploads, outputs, and storage accounting remain correct over time.

Status: Completed on 2026-03-08

### Tasks

- delete associated files when deleting jobs
- verify storage counters against actual filesystem state
- remove duplicate or unnecessary file copies where safe
- add cleanup strategy for stale temp/intermediate files
- validate quota enforcement against real storage usage

### Exit Criteria

- deleting a job removes its related files
- storage usage remains consistent
- temp/output growth is controlled

Completion notes:
- centralized job artifact discovery and cleanup in the backend service layer
- job deletion now removes job input copies, intermediate JSON artifacts, extracted temp directories, and final output directories before deleting the DB row
- user storage is now recalculated from actual filesystem state instead of relying on stale manual counters
- upload, assemble, generation, user stats, and current-user/profile responses now sync storage from the filesystem source of truth
- generation now removes original upload folders after job creation so job copies become the canonical inputs and duplicate input storage is reduced
- Celery task completion and failure paths now resync storage after runtime artifacts are created
- added explicit stale-runtime cleanup support for temp extraction and intermediate artifacts
- expanded the developer cleanup script to cover `inputs/` and structured output directories
- validated backend import sanity
- validated targeted Python compilation for the changed backend modules

## Phase 5 - Pipeline Hardening

### Objective

Make report generation more reliable across supported project types and reduce hallucination/isolation failures.

### Tasks

- define supported project categories explicitly
- strengthen deterministic pre-LLM analysis
- verify project isolation boundaries across parser/planner/writer/builder
- tighten JSON contracts between stages
- add graceful fallback behavior for sparse, partial, or unsupported inputs
- improve builder robustness for malformed or partial content
- review prompt constraints where failures are prompt-driven instead of code-driven

### Exit Criteria

- pipeline handles expected project categories consistently
- unsupported cases fail clearly instead of silently degrading
- per-job isolation is preserved end to end

Completion notes:
- added deterministic support-tier classification in `utils/facts_builder.py` so sparse or weakly supported projects are labeled before any LLM stage runs
- planner and writer agents now support deterministic reduced-scope outline/content generation for reduced or unsupported inputs
- Celery pipeline orchestration now branches explicitly into reduced-scope planner/writer execution instead of always forcing the full LLM path
- added focused regression coverage for support classification and reduced-scope planner/writer behavior in `tests/test_pipeline_hardening.py`
- validated targeted Python compilation, deterministic pipeline tests, and backend import sanity with explicit writable runtime paths
- default backend startup still relies on runtime directory/database writes, which reinforces the need for Phase 6 backend production hardening

## Phase 6 - Backend Production Hardening

### Objective

Replace prototype backend patterns with production-safe infrastructure assumptions.

### Tasks

- remove `Base.metadata.create_all()` from runtime startup
- require Alembic migrations for schema changes
- validate PostgreSQL-first deployment path
- harden Redis/Celery operational behavior
- improve error handling and structured logging
- add rate limiting and abuse protection where needed
- review auth/session/OAuth configuration safety

### Exit Criteria

- backend startup is migration-safe
- deployment assumptions are explicit
- core services are observable and operationally sane

## Phase 7 - Automated Validation

### Objective

Add regression coverage for the highest-risk user flows.

### Tasks

- add frontend build check to routine validation
- add API contract tests for key routes
- add WebSocket flow tests
- add storage lifecycle tests
- add end-to-end report generation tests for representative project types
- define smoke tests for auth, upload, processing, success, sharing, and history flows

### Exit Criteria

- major regressions are caught before merge
- pipeline and UI critical paths have automated coverage

## Phase 8 - Product Polish

### Objective

Improve user-facing reliability, clarity, and recovery.

### Tasks

- improve upload validation and failure messaging
- improve failed-job recovery paths
- improve report history and sharing UX
- review dashboard metrics clarity
- improve status visibility for long-running jobs
- document supported inputs and limitations clearly

### Exit Criteria

- user-facing flows are coherent
- failures are explainable
- the product feels stable, not experimental

## Priority Order

Recommended execution order:

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 4
6. Phase 5
7. Phase 6
8. Phase 7
9. Phase 8

## Immediate Focus

If execution starts now, the best first block is:

1. pipeline hardening follow-up
2. backend production hardening preparation
3. automated validation expansion
4. product polish follow-up

## Notes

- This document is the planning source of truth.
- Execution details should be logged in `docs/WORK_EXECUTION_TRACKER.md`.
- When a phase starts or finishes, update both files.
