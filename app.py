from quart import Quart, request, Response

from loguru import logger
from renderer import svg_to_png

app = Quart(__name__)

# SVG 字符串中内嵌了 base64 图片，单次请求体可能较大，设置 4MB 上限
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/render")
async def render() -> Response:
    """接收 SVG 字符串，返回渲染后的 PNG 图片。

    请求体: JSON {"svg": "<svg>...</svg>"}
    响应:   image/png bytes
    """
    data = await request.get_json()
    if not data or "svg" not in data:
        return Response("missing 'svg' field in request body", status=400)

    svg_string: str = data["svg"]
    if not svg_string.strip():
        return Response("empty svg string", status=400)

    try:
        png_bytes = await svg_to_png(svg_string)
    except Exception as e:
        logger.error("渲染 SVG 失败: {}", e, exc_info=True)
        return Response(f"render failed: {e}", status=500)

    return Response(png_bytes, content_type="image/png")
