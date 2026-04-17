#!/usr/bin/env python3
"""
image_meta_mcp — MCP server for reading image generation metadata.
Supports PNG (tEXt/iTXt chunks) and JPEG (EXIF/UserComment).
"""

import logging
import os
import struct
import zlib
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from PIL import Image

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log_path = Path.home() / "Library" / "Logs" / "Claude" / "mcp-server-image-meta.log"
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(log_path),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("image_meta")

# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def extract_png_metadata(path: Path) -> dict:
    """Extract tEXt/iTXt chunks from a PNG via Pillow's image.info."""
    img = Image.open(path)
    img.verify()  # Raises if file is corrupt
    # Re-open after verify (verify closes the file)
    img = Image.open(path)
    info = img.info
    if not info:
        return {}
    return {k: v for k, v in info.items() if isinstance(v, (str, bytes))}


def extract_jpeg_metadata(path: Path) -> dict:
    """Extract EXIF and UserComment from a JPEG."""
    img = Image.open(path)
    result = {}

    # Pillow exposes some JPEG metadata via info
    if img.info:
        for k, v in img.info.items():
            if isinstance(v, (str, bytes)):
                result[k] = v

    # Try EXIF via Pillow's getexif()
    try:
        exif = img.getexif()
        if exif:
            from PIL.ExifTags import TAGS
            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                if isinstance(value, (str, bytes, int, float)):
                    result[f"exif:{tag_name}"] = value
    except Exception as e:
        log.debug("EXIF extraction failed: %s", e)

    return result


def format_metadata(meta: dict) -> str:
    """Format metadata dict into readable text."""
    lines = []
    for key, value in meta.items():
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8", errors="replace")
            except Exception:
                value = repr(value)
        lines.append(f"[{key}]\n{value}")
    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# MCP tool handler
# ---------------------------------------------------------------------------

def read_image_metadata(file_path: str) -> str:
    log.info("read_image_metadata called: %s", file_path)

    path = Path(file_path).expanduser().resolve()

    # File not found
    if not path.exists():
        msg = f"File not found: {path}. Check the path and try again. See log for details: {log_path}"
        log.error(msg)
        return msg

    # Format check
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        msg = (
            f"Unsupported file type '{suffix}'. Supported: .png, .jpg, .jpeg. "
            f"See log for details: {log_path}"
        )
        log.error(msg)
        return msg

    # Extract
    try:
        if suffix == ".png":
            meta = extract_png_metadata(path)
        else:
            meta = extract_jpeg_metadata(path)
    except Exception as e:
        msg = f"Failed to read image '{path.name}': {e}. See log for details: {log_path}"
        log.exception("Extraction error")
        return msg

    # No metadata found
    if not meta:
        if suffix in {".jpg", ".jpeg"}:
            return (
                f"No metadata found in '{path.name}'. "
                "JPEG files may not carry SD generation parameters unless explicitly embedded (e.g. CivitAI). "
                f"See log for details: {log_path}"
            )
        return (
            f"No metadata found in '{path.name}'. "
            "The image may have been saved without generation parameters. "
            f"See log for details: {log_path}"
        )

    log.info("Metadata extracted successfully: %d keys", len(meta))
    return format_metadata(meta)


# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

server = Server("image-meta")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="read_image_metadata",
            description=(
                "Read embedded metadata from a PNG or JPEG image file. "
                "Returns generation parameters (prompt, negative prompt, sampler, seed, etc.) "
                "as embedded by Stable Diffusion, ComfyUI, CivitAI, and similar tools. "
                "Provide the full absolute path to the image file."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the image file (PNG or JPEG).",
                    }
                },
                "required": ["file_path"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "read_image_metadata":
        result = read_image_metadata(arguments.get("file_path", ""))
        return [TextContent(type="text", text=result)]
    raise ValueError(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    log.info("image_meta_mcp server starting")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
