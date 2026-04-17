# image-meta-mcp — Image Metadata MCP Server

An [MCP](https://modelcontextprotocol.io) server that provides image metadata reading tools to Claude Desktop. Extracts generation parameters embedded by Stable Diffusion, ComfyUI, CivitAI, and similar tools.

## Tools

| Tool | Description |
| --- | --- |
| `read_image_metadata(file_path)` | Read embedded metadata from a PNG or JPEG (prompt, negative prompt, sampler, seed, etc.) |

## Requirements

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) package manager

## Supported Formats

| Format | Metadata source |
| --- | --- |
| PNG | tEXt/iTXt chunks via Pillow `image.info` |
| JPEG | EXIF tags + UserComment via Pillow `getexif()` |

## Setup

### 1. Install uv (if not already installed)

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and install dependencies

```
git clone https://github.com/YOUR_USERNAME/image-meta-mcp.git
cd image-meta-mcp
uv sync
```

### 3. Verify the install

```
uv run python check_env.py
```

### 4. Configure Claude Desktop

Edit your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the following under `"mcpServers"`:

```json
{
  "mcpServers": {
    "image-meta": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/image-meta-mcp",
        "python",
        "image_server.py"
      ]
    }
  }
}
```

Replace `/absolute/path/to/image-meta-mcp` with the actual path where you cloned the repo.

### 5. Restart Claude Desktop

The `read_image_metadata` tool will appear in Claude's tool list when connected.

## Usage

Provide the absolute path to a PNG or JPEG:

```
read the metadata from /Users/yourname/Pictures/output.png
```

## Logs

`~/Library/Logs/Claude/mcp-server-image-meta.log`

## Notes

- JPEG files may not carry SD generation parameters unless explicitly embedded (e.g. by CivitAI)
- PNG is the primary format for SD/ComfyUI generation metadata
