# 学生信息管理系统

基于 FastAPI 的可部署学生信息管理系统，建立在原有 SQLite 学生数据和增删改查功能基础上，新增网页管理、登录注册、角色权限、成绩图表和 Excel 报表。

## 功能

- FastAPI 网页管理
- 学生信息增删改查
- 学号或姓名搜索
- 成绩统计和 Chart.js 图表
- Excel 导入和导出
- 用户注册和登录
- 管理员、教师、查看者三种角色
- 管理员调整用户权限
- CSRF 防护和密码哈希
- SQLite 默认存储，支持通过环境变量切换数据库路径
- Docker 和 Docker Compose 部署
- Swagger API 文档：`/docs`

## 快速运行

```bash
python -m venv .venv
.
venv\Scripts\activate
pip install -r requirements-web.txt
uvicorn webapp.main:app --reload
```

打开 `http://127.0.0.1:8000`。

默认管理员账号为 `admin`，初始密码为 `admin123`。部署到公网前，必须通过 `ADMIN_INITIAL_PASSWORD` 和 `SECRET_KEY` 环境变量修改默认配置。

## Docker 部署

```bash
docker compose up -d --build
```

生产环境建议设置：

```text
SECRET_KEY=随机生成的长密钥
ADMIN_INITIAL_PASSWORD=强密码
COOKIE_SECURE=1
DATABASE_PATH=/data/students.db
```

部署到公网需要把项目运行在云主机或支持 Docker 的平台上，并配置 HTTPS、持久化磁盘和 PostgreSQL 数据库。当前代码默认使用 SQLite，适合演示和小规模使用；多人长期公网使用时建议切换到 PostgreSQL。

## Excel 格式

导入文件第一行必须是：

```text
学号 | 姓名 | 年龄 | 成绩
```

重复学号会更新已有记录。

## 权限

| 角色 | 查看和搜索 | 添加修改删除 | Excel 导入导出 | 用户权限管理 |
| --- | --- | --- | --- | --- |
| 管理员 | 是 | 是 | 是 | 是 |
| 教师 | 是 | 是 | 是 | 否 |
| 查看者 | 是 | 否 | 可导出 | 否 |

新注册用户默认为查看者。

## 测试

```bash
python -m unittest -v test_database.py test_webapp.py
```

## 参考项目

本项目参考了 FastAPI 官方全栈模板的认证、测试和 Docker 组织方式，以及 SQLAdmin、FastAPI Admin 等开源项目的后台管理思路。代码按本项目需求重新实现，不直接复制第三方项目代码。
