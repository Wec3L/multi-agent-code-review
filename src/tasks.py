import json
import sys
from pathlib import Path

DB_FILE = Path(__file__).parent / "tasks.json"


def load_tasks():
    if not DB_FILE.exists():
        return []
    return json.loads(DB_FILE.read_text(encoding="utf-8"))


def save_tasks(tasks):
    DB_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def add_task(title):
    if not title.strip():
        raise ValueError("Task title must not be empty")
    tasks = load_tasks()
    new_id = max([t["id"] for t in tasks], default=0) + 1
    tasks.append({"id": new_id, "title": title, "done": False})
    save_tasks(tasks)
    return new_id


def list_tasks():
    return load_tasks()


def complete_task(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            save_tasks(tasks)
            return True
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python tasks.py [add <title> | list | done <id>]")
        return 1

    command = sys.argv[1]

    if command == "add":
        title = " ".join(sys.argv[2:])
        try:
            task_id = add_task(title)
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 1
        print(f"Added task #{task_id}: {title}")
    elif command == "list":
        if len(sys.argv) != 2:
            print("Usage: python tasks.py list", file=sys.stderr)
            return 1
        for t in list_tasks():
            mark = "x" if t["done"] else " "
            print(f"[{mark}] {t['id']}. {t['title']}")
    elif command == "done":
        if len(sys.argv) != 3:
            print("Usage: python tasks.py done <id>", file=sys.stderr)
            return 1
        try:
            task_id = int(sys.argv[2])
        except ValueError:
            print("Task ID must be an integer", file=sys.stderr)
            return 1
        if complete_task(task_id):
            print(f"Task #{task_id} completed")
        else:
            print(f"Task #{task_id} not found")
            return 1
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
