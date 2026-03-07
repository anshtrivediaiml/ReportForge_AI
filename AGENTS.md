## Codex Skill Routing

Use the repo-specific Codex skills installed under `C:\Users\AnshTrivedi\.codex\skills` when they match the task.

### Use `$report-pipeline`

Use for end-to-end report generation flow, cross-agent issues, intermediate JSON artifacts, project isolation bugs, or full pipeline changes touching:
- `api/app/tasks/report_tasks.py`
- `agents/`
- `utils/code_analyzer.py`
- `utils/pdf_parser.py`
- `tests/test_full_pipeline.py`

### Use `$report-prompts`

Use for prompt engineering, JSON response contracts, anti-hallucination rules, chapter/section generation behavior, or any change centered on:
- `config/prompts.py`

### Use `$report-docx-builder`

Use for DOCX assembly, formatting, title page, table of contents, references, figures, tables, or final document rendering work touching:
- `agents/builder_agent.py`
- `utils/docx_generator.py`

### Use `$report-api-backend`

Use for FastAPI, Celery, database models, auth, uploads, websocket progress, analytics, sharing, or backend job lifecycle work touching:
- `api/app/`

### Use `$report-frontend`

Use for React pages, components, Zustand stores, API integration, auth UI, upload flow, processing dashboard, or frontend websocket behavior touching:
- `web/`

## Coordination Rules

- If a request spans multiple layers, use the smallest set of relevant skills.
- Prefer `$report-pipeline` for cross-agent or stage-handoff issues.
- Prefer `$report-prompts` when the root problem is model behavior instead of Python control flow.
- Prefer `$report-api-backend` and `$report-frontend` together only when changing an API contract and its UI consumer in the same task.
- Prefer `$report-docx-builder` only when content already exists and the main issue is rendering or document structure.
