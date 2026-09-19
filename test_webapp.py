import os
import tempfile
import unittest
from pathlib import Path


class WebAppSmokeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_PATH"] = str(Path(cls.temp_dir.name) / "test.db")
        from fastapi.testclient import TestClient
        from webapp.main import app
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_login_page_and_register_flow(self):
        self.client.get("/logout")
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        csrf = self._csrf(response.text)
        response = self.client.post(
            "/register",
            data={
                "csrf_token": csrf,
                "username": "teacher1",
                "full_name": "测试教师",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/login")

    def test_admin_can_login_and_view_students(self):
        self.client.get("/logout")
        response = self.client.get("/login")
        csrf = self._csrf(response.text)
        response = self.client.post(
            "/login",
            data={"csrf_token": csrf, "username": "admin", "password": "admin123"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        response = self.client.get("/students")
        self.assertEqual(response.status_code, 200)
        self.assertIn("学生管理", response.text)

    def test_admin_can_create_search_stats_and_export(self):
        self.client.get("/logout")
        login_page = self.client.get("/login")
        csrf = self._csrf(login_page.text)
        self.client.post(
            "/login",
            data={"csrf_token": csrf, "username": "admin", "password": "admin123"},
        )
        students_page = self.client.get("/students")
        csrf = self._csrf(students_page.text)
        response = self.client.post(
            "/students/create",
            data={
                "csrf_token": csrf,
                "student_id": "TEST001",
                "name": "测试学生",
                "age": "20",
                "score": "92",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        self.assertIn("TEST001", self.client.get("/students?q=TEST001").text)
        stats = self.client.get("/api/stats").json()
        self.assertGreaterEqual(stats["count"], 1)
        export = self.client.get("/students/export")
        self.assertEqual(export.status_code, 200)
        self.assertEqual(
            export.headers["content-type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    @staticmethod
    def _csrf(html):
        marker = 'name="csrf_token" value="'
        start = html.index(marker) + len(marker)
        return html[start:html.index('"', start)]


if __name__ == "__main__":
    unittest.main()
