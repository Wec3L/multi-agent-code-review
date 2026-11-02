import json
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PROJECT_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_DIR / ".workflow" / "state.json"
ALLOWED_STATUSES = {"running", "done", "failed"}

mcp = FastMCP("workflow")


def load_state():
    if not STATE_FILE.exists():
        return {"agents": {}, "events": []}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


@mcp.tool()
def report_step(agent: str, status: str, summary: str) -> str:
    """Сообщить статус шага конвейера. agent: conductor/developer/tester/reviewer/documenter. status: running/done/failed. summary: одна строка о том, что происходит."""
    if status not in ALLOWED_STATUSES:
        return f"Ошибка: статус должен быть одним из {sorted(ALLOWED_STATUSES)}"

    state = load_state()
    now = datetime.now().strftime("%H:%M:%S")
    state["agents"][agent] = {"status": status, "summary": summary, "time": now}
    state["events"].append({"time": now, "agent": agent, "status": status, "summary": summary})
    save_state(state)
    return f"OK: {agent} -> {status}"


@mcp.tool()
def reset_run() -> str:
    """Сбросить состояние прогона: все агенты снова в ожидании."""
    save_state({"agents": {}, "events": []})
    return "OK: прогон сброшен"


if __name__ == "__main__":
    mcp.run()
    # report_step: инструмент MCP-сервера. Агент вызывает его сам в начале и в конце своей работы. Сообщает, кто работает, в каком статусе и что делает. Сервер записывает это в .workflow/state.json.