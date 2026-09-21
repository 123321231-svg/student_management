# 从命令行版到 FastAPI 版

`9c24386` 版本通过函数调用完成增删改查；网页版本把同样的业务能力放到 HTTP 请求中。

| 命令行概念 | Web 对应概念 |
| --- | --- |
| `input()` | HTML 表单或 JSON 请求体 |
| 菜单编号 | URL 路由 |
| `print()` | HTML 模板或 JSON 响应 |
| 数据库函数 | Repository / SQLAlchemy Session |
| `try/except` 提示 | HTTP 状态码和页面消息 |
| 单用户运行 | 登录、会话和角色权限 |

学习时先找到两个版本中完成同一件事的代码，再观察 Web 版本新增了哪些输入校验、安全和并发边界。
