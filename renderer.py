import asyncio
import threading

from loguru import logger
from playwright.sync_api import sync_playwright, Playwright, Browser, Page


class SVGRenderer:
    """基于 Playwright/Chromium 的 SVG 渲染器。

    在首次调用时懒初始化 Chromium 实例，后续复用同一个 page 对象，
    避免每次渲染都启动浏览器的开销。
    """

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None
        self._lock = threading.Lock()

    def _ensure_browser(self) -> Page:
        """懒初始化：首次调用时才启动 Chromium，后续直接复用。"""
        if self._page is not None:
            return self._page
        with self._lock:
            if self._page is not None:
                return self._page
            logger.info("SVGRenderer: 正在启动 Chromium ...")
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch()
            self._page = self._browser.new_page()
            logger.info("SVGRenderer: Chromium 已就绪")
            return self._page

    def render_to_bytes(self, svg_string: str) -> bytes:
        """将 SVG 字符串渲染为 PNG bytes（同步方法，需在线程中调用）。"""
        page = self._ensure_browser()
        html_content = (
            "<!DOCTYPE html>"
            "<html><head><meta charset='utf-8'></head>"
            f"<body style='margin:0;padding:0;background:transparent;'>{svg_string}</body></html>"
        )
        page.set_content(html_content, wait_until="networkidle")
        png_bytes: bytes = page.locator("svg").screenshot(
            omit_background=True, type="png"
        )
        return png_bytes

    def close(self) -> None:
        """释放 Chromium 资源。"""
        with self._lock:
            if self._browser:
                self._browser.close()
                self._browser = None
            if self._playwright:
                self._playwright.stop()
                self._playwright = None
            self._page = None
            logger.info("SVGRenderer: 已关闭")


# 全局单例：进程生命周期内复用，避免重复启动 Chromium
_renderer = SVGRenderer()


async def svg_to_png(svg_string: str) -> bytes:
    """异步将 SVG 字符串渲染为 PNG bytes。

    内部通过 asyncio.to_thread 将同步的 Playwright 调用放到线程池，
    不会阻塞事件循环。
    """
    return await asyncio.to_thread(_renderer.render_to_bytes, svg_string)
