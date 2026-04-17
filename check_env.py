#!/usr/bin/env python3
"""
Verify that the image_meta_mcp environment is set up correctly.
Run with: uv run python check_env.py
"""

import sys

print(f"Python: {sys.version}")

try:
    from mcp.server import Server
    import mcp
    print(f"mcp: OK ({mcp.__version__})")
except ImportError as e:
    print(f"mcp: MISSING — {e}")
    sys.exit(1)

try:
    from PIL import Image
    import PIL
    print(f"Pillow: OK ({PIL.__version__})")
except ImportError as e:
    print(f"Pillow: MISSING — {e}")
    sys.exit(1)

try:
    from image_server import read_image_metadata, SUPPORTED_EXTENSIONS
    print(f"image_server: OK (supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))})")
except ImportError as e:
    print(f"image_server: MISSING — {e}")
    sys.exit(1)

print("\nAll checks passed. Ready to connect to Claude Desktop.")
