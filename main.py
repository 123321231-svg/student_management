from database import StudentDatabase
from analysis import data_analysis
from api import test_api


def input_non_empty(prompt, field_name):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print(f"{field_name}不能为空")


def parse_age(value):
    age = int(value)
    if age <= 0:
        raise ValueError("年龄必须大于0")
    return age


def parse_score(value):
    score = float(value)
    if score < 0 or score > 100:
        raise ValueError("成绩必须在0~100之间")
    return score


def input_age():
    while True:
        try:
            return parse_age(input("请输入年龄："))
        except ValueError:
            print("年龄必须是大于0的整数")


def input_score():
    while True:
        try:
            return parse_score(input("请输入成绩："))
        except ValueError:
            print("成绩必须是0~100之间的数字")


def input_optional(prompt, current_value, parser):
    value = input(f"{prompt}（直接回车保留：{current_value}）：").strip()
    if not value:
        return current_value
    while True:
        try:
            return parser(value)
        except ValueError as error:
            print(error)
            value = input("请重新输入（直接回车保留原值）：").strip()
            if not value:
                return current_value


def add_student(db):
    print("\n========== 添加学生 ==========")
    student_id = input_non_empty("请输入学号：", "学号")
    name = input_non_empty("请输入姓名：", "姓名")
    success, message = db.add_student(student_id, name, input_age(), input_score())
    print(message)


def show_students(db):
    print("\n========== 学生列表 ==========")
    students = db.get_all_students()
    if not students:
        print("暂无学生信息")
        return
    for student in students:
        print(f"学号：{student[0]} | 姓名：{student[1]} | 年龄：{student[2]} | 成绩：{student[3]}")


def find_student(db):
    print("\n========== 查询学生 ==========")
    student = db.get_student(input_non_empty("请输入学号：", "学号"))
    if student:
        print("\n查询结果：")
        print("学号：", student[0])
        print("姓名：", student[1])
        print("年龄：", student[2])
        print("成绩：", student[3])
    else:
        print("没有找到该学生")


def update_student(db):
    print("\n========== 修改学生 ==========")
    student_id = input_non_empty("请输入学号：", "学号")
    student = db.get_student(student_id)
    if not student:
        print("学生不存在")
        return
    print("当前姓名：", student[1])
    print("当前年龄：", student[2])
    print("当前成绩：", student[3])
    name = input_optional("请输入新的姓名", student[1], str)
    age = input_optional("请输入新的年龄", student[2], parse_age)
    score = input_optional("请输入新的成绩", student[3], parse_score)
    success, message = db.update_student(student_id, name, age, score)
    print(message)


def delete_student(db):
    print("\n========== 删除学生 ==========")
    student_id = input_non_empty("请输入学号：", "学号")
    student = db.get_student(student_id)
    if not student:
        print("学生不存在")
        return
    print(f"即将删除：{student[1]}（{student[0]}）")
    if input("确定删除吗？(y/n)：").lower() != "y":
        print("已取消")
        return
    success, message = db.delete_student(student_id)
    print(message)


def show_menu():
    print("""
========================================
          学生信息管理系统
========================================

1. 添加学生
2. 查看所有学生
3. 查询学生
4. 修改学生
5. 删除学生
6. 数据分析
7. HTTP/API测试
0. 退出

========================================
""")


def main():
    db = StudentDatabase()
    try:
        while True:
            show_menu()
            choice = input("请选择功能：")
            if choice == "1":
                add_student(db)
            elif choice == "2":
                show_students(db)
            elif choice == "3":
                find_student(db)
            elif choice == "4":
                update_student(db)
            elif choice == "5":
                delete_student(db)
            elif choice == "6":
                data_analysis(db.conn)
            elif choice == "7":
                test_api()
            elif choice == "0":
                print("程序结束")
                break
            else:
                print("输入错误，请重新选择")
    finally:
        db.close()


if __name__ == "__main__":
    main()
