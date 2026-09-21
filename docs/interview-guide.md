# 面试指南

## 30 秒项目介绍

这是一个从 Python + SQLite 命令行程序演进而来的学生学业数据分析平台。后端使用 FastAPI 和 SQLAlchemy，支持三级权限、教务数据管理、Excel 报表和审计日志；Pandas 负责成绩趋势、数据质量和可解释风险分析。项目包含自动测试、Docker、数据库迁移和 Windows 便携发布流程。

## 常见问题

### 为什么选择 FastAPI？

它有类型提示、Pydantic 校验和自动 OpenAPI 文档，适合同时提供网页和 REST API，也方便测试异步或同步接口。

### 为什么使用 Service/Analytics 模块？

如果统计公式全部写在路由中，只能通过 HTTP 测试。抽离后可以用普通 Python 输入直接验证规则，并在网页、API、脚本中复用。

### SQLite 和 PostgreSQL 如何选择？

SQLite 零配置，适合学习、自动测试和 EXE；PostgreSQL 更适合多人并发和正式部署。SQLAlchemy 让核心领域模型可以在两者之间切换。

### 如何保证权限安全？

服务端每次写操作都重新检查登录状态和角色，不能依赖前端隐藏按钮。网页写操作使用 CSRF Token，密码使用 scrypt 加盐哈希。

### 风险预警为什么不用机器学习？

当前数据量和标签不足，机器学习结果难以验证。透明规则可以解释、测试和调整，未来有真实历史数据后再比较规则与模型效果。

### 遇到过什么实际问题？

SQLAlchemy 默认连接池在 Windows 测试中会保留 SQLite 文件句柄，导致临时目录无法删除。通过复现和连接生命周期分析，SQLite 改用 NullPool，PostgreSQL 仍使用连接池。
