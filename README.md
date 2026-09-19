# 学生信息管理系统

一个基于 Python 开发的命令行学生信息管理系统。

## 运行

在项目目录中执行：

```bash
python main.py
```

默认数据库文件为项目目录下的 `students.db`，从其他目录启动时仍会使用同一个数据库。

## 项目功能

- 添加学生
- 查看所有学生
- 查询学生
- 修改学生
- 删除学生
- 成绩统计
- 成绩排行榜
- HTTP/API 测试
- SQLite 数据库存储

## 测试

```bash
python -m unittest -v test_database.py
```

## 技术栈

- Python
- SQLite
- SQL
- Pandas
- Requests

## 项目结构

```text
student-management-system/
│
├── main.py
├── database.py
├── analysis.py
├── api.py
├── test_database.py
├── requirements.txt
├── README.md
└── .gitignore
```
