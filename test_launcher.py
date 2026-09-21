import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class DesktopLauncherTest(unittest.TestCase):
    def test_check_command_reports_available_port(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "desktop_launcher.py"), "--check"],
            capture_output=True,
            text=True,
            timeout=15,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertIsInstance(payload["available_port"], int)
        self.assertGreater(payload["available_port"], 0)

    def test_launcher_loads_application_object_for_frozen_build(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["DATABASE_PATH"] = str(Path(temp_dir) / "launcher-test.db")
            from desktop_launcher import load_application
            from webapp.main import app

            self.assertIs(load_application(), app)


if __name__ == "__main__":
    unittest.main()
