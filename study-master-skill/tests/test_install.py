import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL_SCRIPT = ROOT / "install.sh"
CLAUDE_HOOK_COMMAND = 'bash "$HOME/.claude/hooks/check-study_master.sh"'


class InstallScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.home = Path(self.temp_dir.name)

        (self.home / ".claude" / "hooks").mkdir(parents=True)
        (self.home / ".claude" / "skills").mkdir(parents=True)
        (self.home / ".agents" / "skills").mkdir(parents=True)
        (self.home / ".codex").mkdir(parents=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_install(self):
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        subprocess.run(
            ["bash", str(INSTALL_SCRIPT)],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def read_json(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_install_cleans_legacy_files_and_normalizes_claude_hook_registration(self):
        settings_path = self.home / ".claude" / "settings.json"
        settings_path.write_text(
            json.dumps(
                {
                    "hooks": {
                        "PostToolUse": [
                            {
                                "matcher": "Write|Edit",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": CLAUDE_HOOK_COMMAND,
                                        "timeout": 10,
                                    },
                                    {
                                        "type": "command",
                                        "command": "echo keep-shared",
                                        "timeout": 5,
                                    },
                                ],
                            },
                            {
                                "matcher": "Write",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": CLAUDE_HOOK_COMMAND,
                                        "timeout": 20,
                                    }
                                ],
                            },
                            {
                                "matcher": "Edit",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "echo keep-edit",
                                        "timeout": 6,
                                    }
                                ],
                            },
                        ]
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        for name in (
            "generate_profiling_report.py",
            "profiling_hook.sh",
            "test_profiling_report.py",
        ):
            (self.home / ".claude" / "hooks" / name).write_text("legacy\n", encoding="utf-8")

        (self.home / ".claude" / "skills" / "study_master").mkdir()
        (self.home / ".agents" / "skills" / "study_master").mkdir()
        (self.home / ".claude" / "skills" / "study_master.md").write_text("legacy\n", encoding="utf-8")

        self.run_install()

        for name in (
            "generate_profiling_report.py",
            "profiling_hook.sh",
            "test_profiling_report.py",
        ):
            self.assertFalse((self.home / ".claude" / "hooks" / name).exists(), name)

        self.assertFalse((self.home / ".claude" / "skills" / "study_master").exists())
        self.assertFalse((self.home / ".agents" / "skills" / "study_master").exists())
        self.assertFalse((self.home / ".claude" / "skills" / "study_master.md").exists())

        settings = self.read_json(settings_path)
        post_tool_use = settings["hooks"]["PostToolUse"]

        occurrences = [
            (entry["matcher"], hook)
            for entry in post_tool_use
            for hook in entry.get("hooks", [])
            if hook.get("command") == CLAUDE_HOOK_COMMAND
        ]
        self.assertEqual(len(occurrences), 1)
        matcher, hook = occurrences[0]
        self.assertEqual(matcher, "Write|Edit")
        self.assertEqual(hook["timeout"], 30)

        shared_entry = next(entry for entry in post_tool_use if entry["matcher"] == "Write|Edit")
        self.assertIn(
            {"type": "command", "command": "echo keep-shared", "timeout": 5},
            shared_entry["hooks"],
        )
        edit_entry = next(entry for entry in post_tool_use if entry["matcher"] == "Edit")
        self.assertEqual(
            edit_entry["hooks"],
            [{"type": "command", "command": "echo keep-edit", "timeout": 6}],
        )


if __name__ == "__main__":
    unittest.main()
