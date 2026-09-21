import json
import subprocess
import sys
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


if __name__ == "__main__":
    unittest.main()
