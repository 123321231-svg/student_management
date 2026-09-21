# 代码地图

## 建议阅读顺序

1. `webapp/security.py`：密码哈希与 CSRF Token。
2. `webapp/services.py`：不依赖网页的校验与统计规则。
3. `webapp/orm.py`：SQLAlchemy 数据模型、关系与会话事务。
4. `webapp/api_v1.py`：版本化 REST API、分页、权限和业务编排。
5. `webapp/analytics.py`：Pandas 趋势与数据质量分析。
6. `webapp/main.py`：网页路由、登录和模板渲染。
7. `desktop_launcher.py`：EXE 如何寻找端口、保存数据并启动服务。

## 一次请求的数据流

```text
浏览器请求 → FastAPI 路由 → 权限检查 → SQLAlchemy 会话
          → 业务/分析函数 → 数据库事务 → JSON 或 Jinja2 页面
```

路由不直接实现统计公式；分析函数不关心 HTTP；模型不负责页面展示。这样的边界让每一层都更容易测试和替换。
