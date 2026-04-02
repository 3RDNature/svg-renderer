# svg-renderer

轻量级 SVG 转 PNG 渲染微服务，基于 Playwright/Chromium 实现高保真截图。

A lightweight SVG-to-PNG rendering microservice powered by Playwright/Chromium for
high-fidelity screenshot rendering.

---

## 目录 / Table of Contents

- [架构概览 / Architecture](#架构概览--architecture)
- [环境要求 / Prerequisites](#环境要求--prerequisites)
- [快速开始 / Quick Start](#快速开始--quick-start)
- [Docker 部署 / Docker Deployment](#docker-部署--docker-deployment)
- [API 接口 / API Reference](#api-接口--api-reference)
- [CI/CD](#cicd)
- [项目结构 / Project Structure](#项目结构--project-structure)
- [技术栈 / Tech Stack](#技术栈--tech-stack)
- [许可证 / License](#许可证--license)

---

## 架构概览 / Architecture

```
HTTP 请求 (Request)
    │
    ▼
┌──────────┐    async/await    ┌──────────────┐   asyncio.to_thread   ┌───────────┐
│  app.py  │ ───────────────▶  │ renderer.py  │ ────────────────────▶  │ Chromium  │
│  (Quart) │                   │ (SVGRenderer)│                        │(Playwright)│
└──────────┘                   └──────────────┘                        └───────────┘
    │                                                                       │
    ◀───────────────────────── PNG bytes ──────────────────────────────────◀─┘
```

- **`app.py`** — HTTP 层：路由定义、请求校验、错误响应。
  HTTP layer: route definitions, request validation, error responses.

- **`renderer.py`** — 渲染层：`SVGRenderer` 单例封装 Playwright/Chromium，懒初始化，
  线程安全。
  Rendering layer: `SVGRenderer` singleton wrapping Playwright/Chromium with lazy
  initialization and thread safety.

Quart 的异步处理器通过 `asyncio.to_thread()` 桥接 Playwright 的同步 API，避免阻塞事件循环。

Quart's async handlers bridge to Playwright's sync API via `asyncio.to_thread()`,
keeping the event loop unblocked.

---

## 环境要求 / Prerequisites

- **Python** >= 3.12
- **[uv](https://github.com/astral-sh/uv)** — 包管理器 / package manager
- **Chromium** — 由 Playwright 自动安装 / auto-installed by Playwright

---

## 快速开始 / Quick Start

### 1. 安装依赖 / Install dependencies

```bash
uv sync
```

### 2. 安装 Chromium 浏览器 / Install Chromium browser

```bash
uv run playwright install --with-deps chromium
```

### 3. 启动服务 / Start the server

```bash
uv run hypercorn -b 0.0.0.0:3000 app:app
```

服务将在 `http://localhost:3000` 上运行。
The server will be available at `http://localhost:3000`.

---

## Docker 部署 / Docker Deployment

```bash
# 构建镜像 / Build image
docker build -t svg-renderer .

# 运行容器 / Run container
docker run -p 3000:3000 svg-renderer
```

---

## API 接口 / API Reference

### 健康检查 / Health Check

```
GET /health
```

**响应 / Response:**

```json
{"status": "ok"}
```

### SVG 渲染 / SVG Rendering

```
POST /render
Content-Type: application/json
```

**请求体 / Request body:**

```json
{
  "svg": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"100\" height=\"100\"><circle cx=\"50\" cy=\"50\" r=\"40\" fill=\"red\"/></svg>"
}
```

**响应 / Response:**

- **成功 (Success):** `200 OK`，返回 `image/png` 二进制数据。
  Returns `image/png` binary data.
- **参数缺失 (Missing field):** `400 Bad Request` — `missing 'svg' field in request body`
- **空字符串 (Empty SVG):** `400 Bad Request` — `empty svg string`
- **渲染失败 (Render failure):** `500 Internal Server Error` — `render failed: <error>`

**请求体大小限制 / Request body size limit:** 4 MB

### 使用示例 / Usage Example

```bash
curl -X POST http://localhost:3000/render \
  -H "Content-Type: application/json" \
  -d '{"svg": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"200\" height=\"200\"><rect width=\"200\" height=\"200\" fill=\"#4A90D9\" rx=\"20\"/><text x=\"100\" y=\"110\" text-anchor=\"middle\" fill=\"white\" font-size=\"24\">Hello SVG</text></svg>"}' \
  --output output.png
```

---

## CI/CD

项目使用 GitHub Actions 实现自动化流水线。
Automated pipelines are powered by GitHub Actions.

### CI — 代码质量检查 / Code Quality Check

在 PR 和 push 到 `main` 时自动运行：
Triggered on PRs and pushes to `main`:

- **Ruff lint** — 静态代码分析 / static code analysis
- **Ruff format** — 代码格式检查 / code formatting check

### CD — 构建并推送 Docker 镜像 / Build & Push Docker Image

在 push 到 `main` 或创建 `v*` tag 时自动运行：
Triggered on pushes to `main` or `v*` tags:

- 构建 Docker 镜像 / Build Docker image
- 推送到 GitHub Container Registry (`ghcr.io`) / Push to ghcr.io
- **标签策略 / Tagging strategy:**
  - `latest` — 每次 push 到 `main` / on every push to `main`
  - `x.y.z`, `x.y`, `x` — 语义化版本，基于 `v*` tag / semver from `v*` tags
  - `<sha>` — 每次构建附带 commit SHA 短标签 / short commit SHA on every build

**拉取镜像 / Pull image:**

```bash
docker pull ghcr.io/<owner>/svg-renderer:latest
```

---

## 项目结构 / Project Structure

```
svg-renderer/
├── .github/
│   └── workflows/
│       ├── ci.yml        # CI: Ruff lint + format check
│       └── cd.yml        # CD: Docker build & push to ghcr.io
├── app.py                # HTTP 服务入口 / HTTP server entry point (Quart)
├── renderer.py           # SVG 渲染逻辑 / SVG rendering logic (Playwright)
├── pyproject.toml        # 项目配置与依赖 / Project config & dependencies
├── uv.lock               # 依赖锁文件 / Dependency lockfile
├── Dockerfile            # 容器构建文件 / Container build file
├── .dockerignore         # Docker 忽略规则 / Docker ignore rules
├── AGENTS.md             # AI 编程代理指南 / AI coding agent guidelines
└── README.md             # 本文件 / This file
```

---

## 技术栈 / Tech Stack

| 依赖 / Package | 用途 / Purpose |
|---|---|
| [Quart](https://quart.palletsprojects.com/) | 异步 Web 框架（Flask 兼容） / Async web framework (Flask-compatible) |
| [Playwright](https://playwright.dev/python/) | 无头浏览器自动化 / Headless browser automation |
| [Loguru](https://github.com/Delgan/loguru) | 结构化日志 / Structured logging |
| [Hypercorn](https://github.com/pgjones/hypercorn) | ASGI 服务器 / ASGI server |
| [uv](https://github.com/astral-sh/uv) | Python 包管理器 / Python package manager |

---

## 许可证 / License

MIT
