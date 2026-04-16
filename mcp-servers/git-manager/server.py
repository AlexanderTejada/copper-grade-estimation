from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from . import git_ops

app = Server("git-manager")

REPO_PATH = str(__import__("pathlib").Path(__file__).parent.parent.parent)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(name="git_status", description="Estado actual del repositorio", inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="git_log", description="Últimos commits", inputSchema={
            "type": "object",
            "properties": {"n": {"type": "integer", "default": 10}},
        }),
        types.Tool(name="git_commit", description="Hace commit con todos los cambios", inputSchema={
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        }),
        types.Tool(name="git_create_branch", description="Crea y cambia a una rama nueva", inputSchema={
            "type": "object",
            "properties": {"branch": {"type": "string"}},
            "required": ["branch"],
        }),
        types.Tool(name="git_diff", description="Muestra los cambios actuales sin commitear", inputSchema={"type": "object", "properties": {}}),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    ops = {
        "git_status": lambda: git_ops.git_status(REPO_PATH),
        "git_log": lambda: git_ops.git_log(REPO_PATH, arguments.get("n", 10)),
        "git_commit": lambda: git_ops.git_commit(REPO_PATH, arguments["message"]),
        "git_create_branch": lambda: git_ops.git_create_branch(REPO_PATH, arguments["branch"]),
        "git_diff": lambda: git_ops.git_diff(REPO_PATH),
    }
    if name not in ops:
        raise ValueError(f"Tool desconocida: {name}")
    return [types.TextContent(type="text", text=ops[name]())]


async def main():
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())
