from pathlib import Path

DOCS_PATH = Path(__file__).parent.parent.parent / "docs"


def ensure_docs_dir() -> None:
    DOCS_PATH.mkdir(exist_ok=True)


def write_doc(filename: str, content: str) -> str:
    ensure_docs_dir()
    path = DOCS_PATH / filename
    path.write_text(content, encoding="utf-8")
    return f"Documento guardado: {path}"


def read_doc(filename: str) -> str:
    path = DOCS_PATH / filename
    if not path.exists():
        raise FileNotFoundError(f"No existe: {filename}")
    return path.read_text(encoding="utf-8")


def list_docs() -> list[str]:
    ensure_docs_dir()
    return [f.name for f in DOCS_PATH.glob("*.md")]


def append_to_doc(filename: str, content: str) -> str:
    ensure_docs_dir()
    path = DOCS_PATH / filename
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{content}")
    return f"Contenido agregado a: {filename}"
