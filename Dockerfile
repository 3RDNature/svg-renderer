FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# 安装 Playwright 浏览器内核 + 系统依赖，并在同一层清理 apt 缓存
RUN uv run playwright install --with-deps chromium && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY . .

EXPOSE 3000
CMD ["uv", "run", "hypercorn", "-b", "0.0.0.0:3000", "app:app"]
