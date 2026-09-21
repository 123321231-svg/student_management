import os
import tempfile
import unittest
import warnings
from pathlib import Path


class WebAppSmokeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_PATH"] = str(Path(cls.temp_dir.name) / "test.db")
        warnings.filterwarnings(
            "ignore",
            message="Using `httpx` with `starlette.testclient` is deprecated",
            category=Warning,
        )
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

    def test_health_endpoint_reports_ready_version(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "student-management", "version": "3.0.1"},
        )

    def test_admin_can_view_audit_log(self):
        self._login_admin()

        response = self.client.get("/audit-logs")

        self.assertEqual(response.status_code, 200)
        self.assertIn("审计日志", response.text)
        self.assertIn("用户登录", response.text)

    def test_admin_cannot_remove_last_admin(self):
        self._login_admin()
        users_page = self.client.get("/users")
        csrf = self._csrf(users_page.text)

        response = self.client.post(
            "/users/1/role",
            data={"csrf_token": csrf, "role": "viewer"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("系统至少需要保留一名管理员", response.text)
        self.assertIn('value="admin" selected', response.text)

    def test_v3_api_requires_authentication(self):
        self.client.get("/logout")

        response = self.client.get("/api/v1/analytics/overview")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "请先登录")

    def test_v3_api_manages_academic_data_and_returns_analytics(self):
        self._login_admin()

        class_response = self.client.post(
            "/api/v1/classes",
            json={"name": "数据科学1班", "grade": "2025", "major": "数据科学"},
        )
        self.assertEqual(class_response.status_code, 201)
        class_id = class_response.json()["id"]

        student_response = self.client.post(
            "/api/v1/students",
            json={
                "student_id": "DS2025001",
                "name": "学习示例",
                "age": 19,
                "class_group_id": class_id,
            },
        )
        self.assertEqual(student_response.status_code, 201)
        student_id = student_response.json()["id"]

        student_list = self.client.get("/api/v1/students?page=1&page_size=1&q=DS2025")
        self.assertEqual(student_list.status_code, 200)
        self.assertEqual(student_list.json()["page"], 1)
        self.assertEqual(student_list.json()["page_size"], 1)
        self.assertGreaterEqual(student_list.json()["total"], 1)
        self.assertEqual(student_list.json()["items"][0]["student_id"], "DS2025001")

        course_response = self.client.post(
            "/api/v1/courses",
            json={"code": "PY101", "name": "Python 数据分析", "credits": 3.0},
        )
        self.assertEqual(course_response.status_code, 201)
        course_id = course_response.json()["id"]

        first_exam = self.client.post(
            "/api/v1/assessments",
            json={"course_id": course_id, "name": "阶段测试一", "exam_date": "2026-03-01"},
        )
        second_exam = self.client.post(
            "/api/v1/assessments",
            json={"course_id": course_id, "name": "阶段测试二", "exam_date": "2026-04-01"},
        )
        self.assertEqual(first_exam.status_code, 201)
        self.assertEqual(second_exam.status_code, 201)

        for assessment, score in ((first_exam, 58), (second_exam, 52)):
            response = self.client.post(
                "/api/v1/scores",
                json={
                    "student_id": student_id,
                    "assessment_id": assessment.json()["id"],
                    "score": score,
                },
            )
            self.assertEqual(response.status_code, 201)

        overview = self.client.get("/api/v1/analytics/overview")
        self.assertEqual(overview.status_code, 200)
        data = overview.json()
        self.assertEqual(data["class_count"], 1)
        self.assertEqual(data["course_count"], 1)
        self.assertEqual(data["assessment_count"], 2)
        self.assertEqual(data["score_count"], 2)
        self.assertEqual(data["average"], 55.0)
        self.assertEqual(data["pass_rate"], 0.0)
        self.assertEqual(data["risk_student_count"], 1)

        trend = self.client.get(f"/api/v1/analytics/students/{student_id}/trend")
        self.assertEqual(trend.status_code, 200)
        self.assertEqual(trend.json()["scores"], [58.0, 52.0])
        self.assertEqual(trend.json()["direction"], "down")
        self.assertEqual(trend.json()["change"], -6.0)
        self.assertIn("连续不及格", trend.json()["risk_reasons"])

        quality = self.client.get("/api/v1/analytics/data-quality")
        self.assertEqual(quality.status_code, 200)
        self.assertGreaterEqual(quality.json()["missing_email_count"], 1)
        self.assertEqual(quality.json()["orphan_score_count"], 0)

    def test_v3_score_rejects_value_above_one_hundred(self):
        self._login_admin()
        response = self.client.post(
            "/api/v1/scores",
            json={"student_id": 1, "assessment_id": 1, "score": 101},
        )

        self.assertEqual(response.status_code, 422)

    def test_v3_academic_and_analytics_pages_are_available(self):
        self._login_admin()

        academics = self.client.get("/academics")
        analytics = self.client.get("/analytics")

        self.assertEqual(academics.status_code, 200)
        self.assertIn("教务数据", academics.text)
        self.assertIn("课程与考试", academics.text)
        self.assertEqual(analytics.status_code, 200)
        self.assertIn("数据分析中心", analytics.text)
        self.assertIn("学业风险", analytics.text)

    def _login_admin(self):
        self.client.get("/logout")
        login_page = self.client.get("/login")
        csrf = self._csrf(login_page.text)
        response = self.client.post(
            "/login",
            data={"csrf_token": csrf, "username": "admin", "password": "admin123"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)

    @staticmethod
    def _csrf(html):
        marker = 'name="csrf_token" value="'
        start = html.index(marker) + len(marker)
        return html[start:html.index('"', start)]


if __name__ == "__main__":
    unittest.main()
