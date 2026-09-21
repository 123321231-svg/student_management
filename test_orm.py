import unittest

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


class OrmSchemaContractTest(unittest.TestCase):
    def test_database_generates_created_at_for_raw_user_insert(self):
        from webapp.orm import Base

        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)

        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO users(username, full_name, password_hash, role)
                        VALUES ('raw-user', '原始 SQL 用户', 'hash', 'viewer')
                        """
                    )
                )
                created_at = conn.execute(
                    text("SELECT created_at FROM users WHERE username = 'raw-user'")
                ).scalar_one()
        except IntegrityError as error:
            self.fail(f"created_at 应由数据库生成，但插入失败：{error}")

        self.assertIsNotNone(created_at)

    def test_database_generates_status_for_raw_student_insert(self):
        from webapp.orm import Base

        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)

        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO students(student_id, name, age, score)
                    VALUES ('S-RAW', '兼容性学生', 20, 88)
                    """
                )
            )
            status = conn.execute(
                text("SELECT status FROM students WHERE student_id = 'S-RAW'")
            ).scalar_one()

        self.assertEqual(status, "active")


if __name__ == "__main__":
    unittest.main()
