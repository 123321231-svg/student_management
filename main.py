from database import StudentDatabase
from analysis import data_analysis
from api import test_api

def input_age():

    while True:

        try:

            age = int(input("请输入年龄："))

            if age <= 0:
                print("年龄必须大于0")
                continue

            return age

        except ValueError:

            print("年龄必须是整数")


def input_score():

    while True:

        try:

            score = float(input("请输入成绩："))

            if score < 0 or score > 100:
                print("成绩必须在0~100之间")
                continue

            return score

        except ValueError:

            print("成绩必须是数字")


def add_student(db):

    print("\n========== 添加学生 ==========")

    student_id = input("请输入学号：")
    name = input("请输入姓名：")

    age = input_age()
    score = input_score()

    success, message = db.add_student(
        student_id,
        name,
        age,
        score
    )
    

    print(message)


def show_students(db):

    print("\n========== 学生列表 ==========")

    students = db.get_all_students()

    if not students:

        print("暂无学生信息")
        return

    for student in students:

        print(
            f"学号：{student[0]} | "
            f"姓名：{student[1]} | "
            f"年龄：{student[2]} | "
            f"成绩：{student[3]}"
        )


def find_student(db):

    print("\n========== 查询学生 ==========")

    student_id = input("请输入学号：")

    student = db.get_student(student_id)

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

    student_id = input("请输入学号：")

    student = db.get_student(student_id)

    if not student:

        print("学生不存在")
        return

    print("当前姓名：", student[1])
    print("当前年龄：", student[2])
    print("当前成绩：", student[3])

    name = input("请输入新的姓名：")
    age = input_age()
    score = input_score()

    success, message = db.update_student(
        student_id,
        name,
        age,
        score
    )

    print(message)


def delete_student(db):

    print("\n========== 删除学生 ==========")

    student_id = input("请输入学号：")

    student = db.get_student(student_id)

    if not student:

        print("学生不存在")
        return

    print(
        f"即将删除："
        f"{student[1]}（{student[0]}）"
    )

    confirm = input("确定删除吗？(y/n)：")

    if confirm.lower() != "y":

        print("已取消")
        return

    success, message = db.delete_student(
        student_id
    )

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
