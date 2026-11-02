import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "src" / "tasks.py"
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("tasks_under_test", SOURCE)
tasks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tasks)


class TasksTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "tasks.json"
        database_patch = patch.object(tasks, "DB_FILE", self.db)
        database_patch.start()
        self.addCleanup(database_patch.stop)

    def cli(self, *arguments):
        output, error = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", [str(SOURCE), *arguments]):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                status = tasks.main()
        return status, output.getvalue() + error.getvalue()

    def test_missing_database_is_empty(self):
        self.assertEqual(tasks.list_tasks(), [])
        self.assertFalse(self.db.exists())

    def test_add_preserves_existing_tasks_and_allocates_max_id(self):
        existing = [{"id": 7, "title": "Купить хлеб", "done": True}]
        tasks.save_tasks(existing)
        self.assertEqual(tasks.add_task("Новая задача"), 8)
        self.assertEqual(tasks.load_tasks(), existing + [
            {"id": 8, "title": "Новая задача", "done": False}
        ])

    def test_empty_title_rejected_without_writing(self):
        for title in ("", " ", "\t\n"):
            with self.subTest(title=title):
                with self.assertRaises(ValueError):
                    tasks.add_task(title)
                self.assertFalse(self.db.exists())

    def test_complete_changes_only_matching_task(self):
        tasks.save_tasks([
            {"id": 1, "title": "one", "done": False},
            {"id": 2, "title": "two", "done": False},
        ])
        self.assertTrue(tasks.complete_task(2))
        self.assertEqual(tasks.load_tasks(), [
            {"id": 1, "title": "one", "done": False},
            {"id": 2, "title": "two", "done": True},
        ])

    def test_cli_successful_add_list_done(self):
        self.assertEqual(self.cli("add", "Buy", "bread"),
                         (0, "Added task #1: Buy bread\n"))
        self.assertEqual(self.cli("list"), (0, "[ ] 1. Buy bread\n"))
        self.assertEqual(self.cli("done", "1"), (0, "Task #1 completed\n"))
        self.assertEqual(self.cli("list"), (0, "[x] 1. Buy bread\n"))

    def test_cli_invalid_arguments_do_not_change_database(self):
        tasks.add_task("Keep me")
        before = self.db.read_bytes()
        cases = [(), ("add",), ("add", "  "), ("list", "extra"),
                 ("done",), ("done", "abc"), ("done", "1.5"),
                 ("done", "1", "extra"), ("unknown",)]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                status, message = self.cli(*arguments)
                self.assertNotEqual(status, 0)
                self.assertTrue(message.strip())
                self.assertNotIn("Traceback", message)
                self.assertEqual(self.db.read_bytes(), before)

    def test_missing_id_does_not_write(self):
        tasks.add_task("Keep me")
        before = self.db.read_bytes()
        self.assertFalse(tasks.complete_task(999))
        self.assertEqual(self.cli("done", "999"),
                         (1, "Task #999 not found\n"))
        self.assertEqual(self.db.read_bytes(), before)

    def test_script_exit_codes(self):
        script = Path(self.directory.name) / "tasks.py"
        script.write_bytes(SOURCE.read_bytes())
        for arguments, expected in [([], 1), (["done", "bad"], 1),
                                    (["add", "Bread"], 0), (["done", "1"], 0),
                                    (["done", "999"], 1), (["list"], 0)]:
            with self.subTest(arguments=arguments):
                result = subprocess.run([sys.executable, str(script), *arguments],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, expected)
                self.assertNotIn("Traceback", result.stderr)

if __name__ == "__main__":
    unittest.main()
