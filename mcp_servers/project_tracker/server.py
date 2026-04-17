from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from . import storage

app = Server("project-tracker")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(name="create_task", description="Crea una tarea nueva", inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "sprint": {"type": "string"},
            },
            "required": ["title", "description"],
        }),
        types.Tool(name="list_tasks", description="Lista tareas, filtrando por sprint o estado", inputSchema={
            "type": "object",
            "properties": {
                "sprint": {"type": "string"},
                "status": {"type": "string", "enum": ["todo", "in_progress", "done"]},
            },
        }),
        types.Tool(name="update_task_status", description="Actualiza el estado de una tarea", inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"},
                "status": {"type": "string", "enum": ["todo", "in_progress", "done"]},
            },
            "required": ["task_id", "status"],
        }),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    storage.init_db()

    if name == "create_task":
        task = storage.create_task(
            title=arguments["title"],
            description=arguments.get("description", ""),
            priority=arguments.get("priority", "medium"),
            sprint=arguments.get("sprint", "backlog"),
        )
        return [types.TextContent(type="text", text=str(task))]

    if name == "list_tasks":
        tasks = storage.list_tasks(
            sprint=arguments.get("sprint"),
            status=arguments.get("status"),
        )
        return [types.TextContent(type="text", text="\n".join(str(t) for t in tasks))]

    if name == "update_task_status":
        task = storage.update_task_status(arguments["task_id"], arguments["status"])
        return [types.TextContent(type="text", text=str(task))]

    raise ValueError(f"Tool desconocida: {name}")


async def main():
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())
