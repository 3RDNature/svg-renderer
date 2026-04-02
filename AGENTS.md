# AGENTS.md — svg-renderer

## Project Overview

Lightweight SVG-to-PNG rendering microservice. A Quart (async Flask) HTTP server
accepts SVG strings via `POST /render` and returns PNG images rendered by a
headless Chromium browser (via Playwright). Python 3.12+, managed by **uv**.

Architecture: two source files only.
- `app.py` — HTTP layer (Quart routes, input validation, error responses)
- `renderer.py` — Rendering logic (`SVGRenderer` class, Playwright/Chromium singleton)

The rendering pipeline bridges async and sync worlds: Quart handlers are
`async def`, Playwright uses its sync API, and `asyncio.to_thread()` bridges them.

---

## Build & Run Commands

| Command | Description |
|---|---|
| `uv sync` | Install/update dependencies from lockfile |
| `uv sync --frozen` | Install dependencies without updating lockfile |
| `uv run playwright install --with-deps chromium` | Install Chromium binary + OS deps |
| `uv run hypercorn -b 0.0.0.0:3000 app:app` | Start the dev server on port 3000 |
| `docker build -t svg-renderer .` | Build the Docker image |
| `docker run -p 3000:3000 svg-renderer` | Run via Docker |

### Testing

There is **no test suite** configured yet. No pytest, unittest, or any test
framework is in the dependencies. If you add tests:

- Add `pytest` and `pytest-asyncio` to `[project.optional-dependencies]` or
  dev dependencies in `pyproject.toml`.
- Place test files in a `tests/` directory following `test_*.py` naming.
- Run all tests: `uv run pytest`
- Run a single test file: `uv run pytest tests/test_renderer.py`
- Run a single test function: `uv run pytest tests/test_renderer.py::test_name`
- Run with verbose output: `uv run pytest -v`

### Linting & Formatting

No linter or formatter is configured in the project. The `.dockerignore`
references `.ruff_cache/`, suggesting **Ruff** is the intended tool. If using Ruff:

- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Auto-fix lint issues: `uv run ruff check --fix .`

### Type Checking

No type checker is configured. The code uses comprehensive type hints (Python
3.10+ union syntax `X | None`). If adding one, use `mypy` or `pyright`:

- `uv run mypy app.py renderer.py`

---

## Code Style Guidelines

### Python Version & Syntax

- Target **Python 3.12+**. Use modern syntax freely (`X | None` instead of
  `Optional[X]`, `match` statements, etc.).

### Formatting

- **4-space indentation** (PEP 8 standard).
- **Double quotes** for all strings — no single quotes.
- **No trailing commas** after the last item in collections/arg lists.
- Keep lines under ~100 characters. Use parenthesized continuation for
  multi-line expressions, not backslash `\`.
- **2 blank lines** between top-level definitions; **1 blank line** between
  methods inside a class.

### Imports

- Group imports in standard PEP 8 order, separated by blank lines:
  1. Standard library (`import asyncio`, `import threading`)
  2. Third-party packages (`from quart import ...`, `from loguru import ...`)
  3. Local modules (`from renderer import svg_to_png`)
- Use **absolute imports** only — no relative imports.
- Use **selective imports** (`from X import Y`) — no wildcard `*` imports.
- No bare `import X` for third-party packages; prefer `from X import ...`.

### Naming Conventions (PEP 8)

| Element | Convention | Example |
|---|---|---|
| Files/modules | `snake_case` | `renderer.py` |
| Classes | `PascalCase` | `SVGRenderer` |
| Functions/methods | `snake_case` | `render_to_bytes` |
| Variables | `snake_case` | `svg_string`, `png_bytes` |
| Private members | `_leading_underscore` | `_renderer`, `self._page` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_CONTENT_LENGTH` |
| Acronyms in class names | Keep uppercase | `SVGRenderer`, not `SvgRenderer` |

### Type Hints

- **Always annotate** function parameters, return types, and non-trivial
  variable assignments.
- Use modern union syntax: `X | None`, not `Optional[X]`.
- Use concrete types — avoid `Any`.
- Import types directly from their source modules (e.g.,
  `from playwright.sync_api import Playwright, Browser, Page`).

### Error Handling

- **Validate inputs early** at the HTTP boundary with guard clauses that
  return 4xx responses immediately.
- **Catch exceptions broadly** only at the outermost boundary layer (HTTP
  handlers). Core logic should let exceptions propagate.
- Log errors with `logger.error(...)` including `exc_info=True` for tracebacks.
- Return meaningful HTTP status codes and error messages in responses.
- Do **not** create custom exception classes unless genuinely needed.

### Async Patterns

- HTTP handlers are `async def`. Always `await` async calls.
- Playwright uses its **sync API** — do not mix with `async_playwright`.
- Bridge sync Playwright calls to async handlers via `asyncio.to_thread()`.
- Use `threading.Lock()` for thread-safe lazy initialization of shared resources.
- Apply double-checked locking for expensive singleton initialization.

### Docstrings & Comments

- Write docstrings on every class and public function (multi-line: summary,
  blank line, elaboration).
- Docstrings and comments are written in **Chinese (Simplified)** — maintain
  this convention for consistency.
- Use free-form prose in docstrings (not Google/NumPy/Sphinx format).
- Use inline comments sparingly, only to explain non-obvious intent.
- Log messages are also in Chinese.

### Architecture Patterns

- **Singleton pattern** for expensive resources (Chromium browser instance).
- **Lazy initialization** — browser starts on first request, not at import time.
- **Separation of concerns** — HTTP/validation logic in `app.py`, rendering
  logic in `renderer.py`. Do not mix web framework code into `renderer.py`.
- `renderer.py` exposes a single public async function (`svg_to_png`) as its
  API. Internal classes and singletons are prefixed with `_`.
- Keep the module structure flat unless complexity demands subdirectories.

### Logging

- Use **loguru** (`from loguru import logger`), not the stdlib `logging` module.
- Use loguru's `{}` placeholder syntax: `logger.info("message: {}", value)`,
  not f-strings or `%` formatting inside log calls.

---

## Dependencies

| Package | Purpose |
|---|---|
| `quart` | Async web framework (Flask-compatible) |
| `playwright` | Headless Chromium browser automation |
| `loguru` | Structured logging |
| `hypercorn` | ASGI server (production) |

Managed by **uv** with `pyproject.toml` + `uv.lock`. Do not add
`requirements.txt`, `setup.py`, or `Pipfile`.

---

## Quick Reference — Health Check

```bash
curl http://localhost:3000/health
# {"status":"ok"}
```

## Quick Reference — Render SVG

```bash
curl -X POST http://localhost:3000/render \
  -H "Content-Type: application/json" \
  -d '{"svg": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"100\" height=\"100\"><circle cx=\"50\" cy=\"50\" r=\"40\" fill=\"red\"/></svg>"}' \
  --output circle.png
```
