from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class Status(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Task:
    id: int
    title: str
    description: str
    status: Status = Status.TODO
    priority: Priority = Priority.MEDIUM
    sprint: str = "backlog"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
