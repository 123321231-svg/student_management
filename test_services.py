import unittest

from webapp.services import student_export_values


class StudentExportValuesTest(unittest.TestCase):
    def test_supports_mapping_rows_returned_by_postgresql(self):
        row = {"student_id": "S001", "name": "张三", "age": 20, "score": 92.5}

        self.assertEqual(student_export_values(row), ["S001", "张三", 20, 92.5])


if __name__ == "__main__":
    unittest.main()
