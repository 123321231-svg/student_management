import sqlite3
import unittest

from database import StudentDatabase


class StudentDatabaseTest(unittest.TestCase):

    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.db = StudentDatabase.__new__(StudentDatabase)
        self.db.conn = self.connection
        self.db.cursor = self.connection.cursor()
        self.db.create_table()

    def tearDown(self):
        self.db.close()

    def test_add_and_get_student(self):
        success, message = self.db.add_student("S001", "张三", 18, 88.5)
        self.assertTrue(success)
        self.assertEqual(message, "学生添加成功")
        self.assertEqual(self.db.get_student("S001"), ("S001", "张三", 18, 88.5))

    def test_duplicate_student_id_is_rejected(self):
        self.db.add_student("S001", "张三", 18, 88.5)
        success, message = self.db.add_student("S001", "李四", 19, 90)
        self.assertFalse(success)
        self.assertEqual(message, "学号已经存在")

    def test_update_and_delete_student(self):
        self.db.add_student("S001", "张三", 18, 88.5)
        success, _ = self.db.update_student("S001", "李四", 19, 91)
        self.assertTrue(success)
        self.assertEqual(self.db.get_student("S001")[1:], ("李四", 19, 91.0))
        success, _ = self.db.delete_student("S001")
        self.assertTrue(success)
        self.assertIsNone(self.db.get_student("S001"))


if __name__ == "__main__":
    unittest.main()
