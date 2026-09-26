import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent import tools


class AgentToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name) / "workspace"
        self.workspace.mkdir()
        self.workspace_patch = patch.object(tools, "WORKSPACE", self.workspace)
        self.workspace_patch.start()

    def tearDown(self):
        self.workspace_patch.stop()
        self.temp_dir.cleanup()

    def test_workspace_path_rejects_traversal_and_absolute_paths(self):
        with self.assertRaises(ValueError):
            tools.workspace_path("../outside.txt")
        with self.assertRaises(ValueError):
            tools.workspace_path(str(Path(self.temp_dir.name) / "outside.txt"))

    def test_preview_file_shows_new_and_changed_content(self):
        target, diff = tools.preview_file("new.txt", "first line\n")
        self.assertEqual(target, (self.workspace / "new.txt").resolve())
        self.assertIn("+first line", diff)

        tools.write_file("new.txt", "old line\n")
        _, diff = tools.preview_file("new.txt", "updated line\n")
        self.assertIn("-old line", diff)
        self.assertIn("+updated line", diff)

    def test_run_python_uses_current_interpreter(self):
        return_code, stdout, stderr = tools.run_python("print('agent-test')")
        self.assertEqual(return_code, 0, stderr)
        self.assertEqual(stdout.strip(), "agent-test")
        self.assertEqual(list(self.workspace.glob("_tmp_*.py")), [])

    def test_parse_actions_extracts_supported_action_blocks(self):
        response = (
            "```create:hello.txt\nhello\n```\n"
            "```shell\necho hello\n```\n"
            "```python:run\nprint('hello')\n```"
        )
        actions = tools.parse_actions(response)
        self.assertEqual([action["type"] for action in actions], ["create", "shell", "python"])


if __name__ == "__main__":
    unittest.main()
