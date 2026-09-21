# 学生学业数据分析与管理平台

[![CI](https://github.com/123321231-svg/student_management/actions/workflows/ci.yml/badge.svg)](https://github.com/123321231-svg/student_management/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/123321231-svg/student_management)](https://github.com/123321231-svg/student_management/releases)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)](https://fastapi.tiangolo.com/)

一个以后端工程和数据分析为主、前端展示为辅的学习型作品集。项目从 Python + SQLite 命令行程序逐步演进为 FastAPI 网页系统，并在 v3.0.0 引入 SQLAlchemy、PostgreSQL、课程/考试领域模型、Pandas 学业分析、版本化 REST API、自动测试、CI 和 Windows EXE。

## 为什么适合作为实习作品集

- **后端能力**：FastAPI、Pydantic 校验、会话认证、RBAC 权限、分层代码、REST API、异常状态码。
- **数据能力**：Pandas 趋势分析、及格率、连续不及格/成绩下降预警、数据质量检查、Excel 报表。
- **数据库能力**：SQLite 零配置运行，SQLAlchemy ORM，PostgreSQL 与 Alembic 迁移支持。
- **工程能力**：单元/集成测试、Ruff、Coverage、Docker Compose、GitHub Actions、自动发布 EXE。
- **可讲解性**：保留命令行、FastAPI 基础版、润色版和求职版的完整 Git 演进路径。

## 主要功能

- 学生信息增删改查、分页和搜索
- 班级、课程、考试与多次成绩数据模型
- 成绩概览、学生趋势、风险原因和数据质量分析
- Chart.js 仪表盘与 Excel 导入导出
- 登录注册，管理员/教师/查看者三级权限
- 最后一名管理员保护、CSRF 防护、密码哈希、审计日志
- `/api/v1` 版本化 API 与 `/docs` 交互文档
- `/health` 健康检查
- SQLite / PostgreSQL 双数据库运行
- Docker 部署与 Windows 单文件 EXE

## 3 分钟运行

需要 Python 3.12+：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-web.txt
uvicorn webapp.main:app --reload
```

打开 `http://127.0.0.1:8000`。默认管理员为 `admin / admin123`，仅供本地学习；公网部署必须设置 `SECRET_KEY` 和 `ADMIN_INITIAL_PASSWORD`。

也可以在 [Releases](https://github.com/123321231-svg/student_management/releases) 下载 Windows 压缩包，解压后双击 `StudentAnalytics.exe`，程序会自动打开浏览器，数据保存在 `%LOCALAPPDATA%\StudentAnalytics`。

## API 示例

登录后访问 `http://127.0.0.1:8000/docs`，可以按顺序创建班级、学生、课程、考试和成绩：

```text
POST /api/v1/classes
POST /api/v1/students
POST /api/v1/courses
POST /api/v1/assessments
POST /api/v1/scores
GET  /api/v1/analytics/overview
GET  /api/v1/analytics/students/{id}/trend
GET  /api/v1/analytics/data-quality
```

## Docker + PostgreSQL

复制环境变量示例并修改密码：

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

Compose 会同时启动应用和 PostgreSQL，浏览器访问 `http://127.0.0.1:8000`。公网环境请使用 HTTPS，并将 `COOKIE_SECURE=1`；数据库和管理员密码不要提交到 Git。

## 权限矩阵

| 角色 | 查看/搜索/分析 | 维护学生与成绩 | Excel 导入 | 用户权限管理 |
| --- | --- | --- | --- | --- |
| 管理员 | 是 | 是 | 是 | 是 |
| 教师 | 是 | 是 | 是 | 否 |
| 查看者 | 是 | 否 | 否 | 否 |

新注册用户默认为查看者。

## 质量检查

```powershell
ruff check webapp desktop_launcher.py test_database.py test_webapp.py test_launcher.py test_orm.py test_services.py
coverage run -m unittest -v test_database.py test_webapp.py test_launcher.py test_orm.py test_services.py
coverage report
```

GitHub Actions 会在每次推送和 Pull Request 时执行相同检查。推送 `v3.*` 标签时，还会在 Windows 环境测试并发布 EXE 压缩包。

## 从代码学习

建议不要一次读完整个仓库，按下面顺序学习：

1. 提交 `9c24386`：你已经理解的命令行版本。
2. 提交 `41255d3`：观察命令行程序如何变成 FastAPI 网页。
3. 标签 `v2.1.0`：学习服务层、权限、审计和测试。
4. 标签 `v3.0.0`：学习 ORM、领域建模、Pandas 分析、API 和工程化。

配套资料：

- [代码地图](docs/code-map.md)
- [从命令行到 FastAPI](docs/from-cli-to-fastapi.md)
- [数据分析学习指南](docs/data-analysis-guide.md)
- [面试问答](docs/interview-guide.md)
- [循序练习题](docs/exercises.md)
- [完整学习路线](docs/learning-guide.md)

## 可写进简历的描述

> 独立开发学生学业数据分析平台，基于 FastAPI、SQLAlchemy 与 PostgreSQL 建模学生、课程、考试和成绩数据；使用 Pandas 实现成绩趋势、及格率、风险预警和数据质量分析；完成 RBAC 权限、审计日志、Excel 报表、Docker 部署、自动化测试及 GitHub Actions 发布流程。

## 项目结构

```text
webapp/main.py       页面、认证和应用入口
webapp/api_v1.py     版本化 REST API
webapp/orm.py        SQLAlchemy 领域模型与数据库会话
webapp/analytics.py  Pandas 分析函数
webapp/services.py   可复用业务规则
migrations/          Alembic 数据库迁移
desktop_launcher.py  Windows EXE 启动器
test_*.py            单元和集成测试
docs/                学习与面试资料
```

本项目参考 FastAPI 官方全栈模板的认证、测试和容器组织思路，代码按本项目需求重新实现，不复制第三方业务代码。

## License

MIT
