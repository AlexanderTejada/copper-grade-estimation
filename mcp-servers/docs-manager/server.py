from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from . import doc_ops

app = Server("docs-manager")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(name="write_doc", description="Crea o sobreescribe un documento .md", inputSchema={
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["filename", "content"],
        }),
        types.Tool(name="read_doc", description="Lee un documento .md", inputSchema={
            "type": "object",
            "properties": {"filename": {"type": "string"}},
            "required": ["filename"],
        }),
        types.Tool(name="list_docs", description="Lista todos los documentos disponibles", inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="append_to_doc", description="Agrega contenido al final de un documento", inputSchema={
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["filename", "content"],
        }),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    ops = {
        "write_doc": lambda: doc_ops.write_doc(arguments["filename"], arguments["content"]),
        "read_doc": lambda: doc_ops.read_doc(arguments["filename"]),
        "list_docs": lambda: "\n".join(doc_ops.list_docs()),
        "append_to_doc": lambda: doc_ops.append_to_doc(arguments["filename"], arguments["content"]),
    }
    if name not in ops:
        raise ValueError(f"Tool desconocida: {name}")
    return [types.TextContent(type="text", text=str(ops[name]()))]


async def main():
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())
