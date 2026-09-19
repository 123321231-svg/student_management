from pathlib import Path
import sqlite3


class StudentDatabase:

    def __init__(self, db_name=None):
        if db_name is None:
            db_name = Path(__file__).resolve().with_name("students.db")
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                score REAL NOT NULL
            )
        """)
        self.conn.commit()

    def add_student(self, student_id, name, age, score):
        try:
            self.cursor.execute("""
                INSERT INTO students (student_id, name, age, score)
                VALUES (?, ?, ?, ?)
            """, (student_id, name, age, score))
            self.conn.commit()
            return True, "学生添加成功"
        except sqlite3.IntegrityError:
            return False, "学号已经存在"

    def get_all_students(self):
        self.cursor.execute("""
            SELECT student_id, name, age, score
            FROM students ORDER BY student_id
        """)
        return self.cursor.fetchall()

    def get_student(self, student_id):
        self.cursor.execute("""
            SELECT student_id, name, age, score
            FROM students WHERE student_id = ?
        """, (student_id,))
        return self.cursor.fetchone()

    def update_student(self, student_id, name, age, score):
        self.cursor.execute("""
            UPDATE students SET name = ?, age = ?, score = ?
            WHERE student_id = ?
        """, (name, age, score, student_id))
        self.conn.commit()
        if self.cursor.rowcount > 0:
            return True, "学生修改成功"
        return False, "学生不存在"

    def delete_student(self, student_id):
        self.cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        self.conn.commit()
        if self.cursor.rowcount > 0:
            return True, "学生删除成功"
        return False, "学生不存在"

    def close(self):
        self.conn.close()
