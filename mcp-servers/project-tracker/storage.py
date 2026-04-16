import psycopg2
from .models import Task, Status, Priority


DB_CONFIG = {
    "host": "localhost",
    "port": 5555,
    "dbname": "copper_tracker",
    "user": "copper_user",
    "password": "copper_pass",
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def init_db() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'todo',
                    priority TEXT DEFAULT 'medium',
                    sprint TEXT DEFAULT 'backlog',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)


def task_from_row(row: tuple) -> Task:
    return Task(
        id=row[0], title=row[1], description=row[2],
        status=Status(row[3]), priority=Priority(row[4]),
        sprint=row[5], created_at=str(row[6]),
    )


def create_task(title: str, description: str, priority: str, sprint: str) -> Task:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title, description, priority, sprint) VALUES (%s, %s, %s, %s) RETURNING id",
                (title, description, priority, sprint),
            )
            return get_task(cur.fetchone()[0])


def get_task(task_id: int) -> Task | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            row = cur.fetchone()
            return task_from_row(row) if row else None


def list_tasks(sprint: str = None, status: str = None) -> list[Task]:
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if sprint:
        query += " AND sprint = %s"
        params.append(sprint)
    if status:
        query += " AND status = %s"
        params.append(status)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return [task_from_row(r) for r in cur.fetchall()]


def update_task_status(task_id: int, status: str) -> Task | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE tasks SET status = %s WHERE id = %s", (status, task_id))
            return get_task(task_id)
