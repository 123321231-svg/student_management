import io
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, File, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook, load_workbook
from starlette.middleware.sessions import SessionMiddleware

from .db import connection, init_db, write_audit
from .security import hash_password, new_csrf_token, verify_password


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app = FastAPI(title="学生信息管理系统", version="2.0.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change-this-secret-key-in-production"),
    https_only=os.getenv("COOKIE_SECURE", "0") == "1",
    same_site="lax",
)


def startup() -> None:
    init_db()


startup()


def csrf(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = new_csrf_token()
        request.session["csrf_token"] = token
    return token


def valid_csrf(request: Request, token: str) -> bool:
    expected = request.session.get("csrf_token", "")
    return bool(token) and secrets.compare_digest(token, expected)


def current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    with connection() as conn:
        return conn.execute(
            "SELECT id, username, full_name, role, is_active FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def render(request: Request, template: str, **context):
    user = current_user(request)
    context.update(
        user=user,
        csrf_token=csrf(request),
        message=request.session.pop("message", None),
    )
    return templates.TemplateResponse(request=request, name=template, context=context)


def redirect_login(message: str | None = None):
    response = RedirectResponse("/login", status_code=303)
    if message:
        response.headers["X-Login-Message"] = message
    return response


def require_user(request: Request):
    user = current_user(request)
    if not user or not user["is_active"]:
        return None
    return user


def require_write_user(request: Request):
    user = require_user(request)
    if not user or user["role"] not in {"admin", "teacher"}:
        return None
    return user


def parse_student(student_id: str, name: str, age: str, score: str):
    student_id = student_id.strip()
    name = name.strip()
    if not student_id or not name:
        raise ValueError("学号和姓名不能为空")
    parsed_age = int(age)
    parsed_score = float(score)
    if parsed_age <= 0:
        raise ValueError("年龄必须大于0")
    if not 0 <= parsed_score <= 100:
        raise ValueError("成绩必须在0到100之间")
    return student_id, name, parsed_age, parsed_score


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return RedirectResponse("/dashboard" if require_user(request) else "/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render(request, "login.html", title="登录")


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
):
    if not valid_csrf(request, csrf_token):
        return render(request, "login.html", title="登录", error="页面已过期，请刷新后重试")
    with connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
        if not user or not user["is_active"] or not verify_password(password, user["password_hash"]):
            return render(request, "login.html", title="登录", error="用户名或密码错误")
        request.session["user_id"] = user["id"]
        write_audit(conn, user["id"], "login", "用户登录")
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return render(request, "register.html", title="注册")


@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    csrf_token: str = Form(...),
):
    if not valid_csrf(request, csrf_token):
        return render(request, "register.html", title="注册", error="页面已过期，请刷新后重试")
    username, full_name = username.strip(), full_name.strip()
    if len(username) < 3 or len(password) < 6 or not full_name:
        return render(request, "register.html", title="注册", error="用户名至少3位，密码至少6位，姓名不能为空")
    if password != confirm_password:
        return render(request, "register.html", title="注册", error="两次输入的密码不一致")
    with connection() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO users(username, full_name, password_hash, role) VALUES (?, ?, ?, 'viewer')",
                (username, full_name, hash_password(password)),
            )
            write_audit(conn, cursor.lastrowid, "register", "用户注册")
        except Exception:
            return render(request, "register.html", title="注册", error="用户名已存在")
    request.session["message"] = "注册成功，请登录"
    return RedirectResponse("/login", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if not require_user(request):
        return redirect_login()
    return render(request, "dashboard.html", title="仪表盘")


@app.get("/students", response_class=HTMLResponse)
def students(request: Request, q: str = Query(default="")):
    if not require_user(request):
        return redirect_login()
    q = q.strip()
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT id, student_id, name, age, score
            FROM students
            WHERE (? = '' OR student_id LIKE ? OR name LIKE ?)
            ORDER BY id DESC
            """,
            (q, f"%{q}%", f"%{q}%"),
        ).fetchall()
    return render(request, "students.html", title="学生管理", students=rows, query=q)


@app.post("/students/create")
def create_student(
    request: Request,
    student_id: str = Form(...),
    name: str = Form(...),
    age: str = Form(...),
    score: str = Form(...),
    csrf_token: str = Form(...),
):
    user = require_write_user(request)
    if not user:
        return RedirectResponse("/students", status_code=303)
    if not valid_csrf(request, csrf_token):
        request.session["message"] = "页面已过期，请刷新后重试"
        return RedirectResponse("/students", status_code=303)
    try:
        values = parse_student(student_id, name, age, score)
        with connection() as conn:
            conn.execute("INSERT INTO students(student_id, name, age, score) VALUES (?, ?, ?, ?)", values)
            write_audit(conn, user["id"], "create_student", f"创建学生 {values[0]}")
        request.session["message"] = "学生添加成功"
    except ValueError as error:
        request.session["message"] = str(error)
    except Exception:
        request.session["message"] = "添加失败，学号可能已经存在"
    return RedirectResponse("/students", status_code=303)


@app.post("/students/{student_id}/update")
def update_student(
    student_id: int,
    request: Request,
    name: str = Form(...),
    age: str = Form(...),
    score: str = Form(...),
    csrf_token: str = Form(...),
):
    user = require_write_user(request)
    if not user:
        return RedirectResponse("/students", status_code=303)
    try:
        values = parse_student("placeholder", name, age, score)
        with connection() as conn:
            conn.execute("UPDATE students SET name = ?, age = ?, score = ? WHERE id = ?", values[1:] + (student_id,))
            write_audit(conn, user["id"], "update_student", f"更新学生记录 {student_id}")
        request.session["message"] = "学生修改成功"
    except ValueError as error:
        request.session["message"] = str(error)
    except Exception:
        request.session["message"] = "学生修改失败"
    return RedirectResponse("/students", status_code=303)


@app.post("/students/{student_id}/delete")
def delete_student(student_id: int, request: Request, csrf_token: str = Form(...)):
    user = require_write_user(request)
    if user and valid_csrf(request, csrf_token):
        with connection() as conn:
            conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
            write_audit(conn, user["id"], "delete_student", f"删除学生记录 {student_id}")
        request.session["message"] = "学生删除成功"
    return RedirectResponse("/students", status_code=303)


@app.get("/students/export")
def export_students(request: Request, q: str = Query(default="")):
    if not require_user(request):
        return redirect_login()
    q = q.strip()
    with connection() as conn:
        rows = conn.execute(
            "SELECT student_id, name, age, score FROM students WHERE (? = '' OR student_id LIKE ? OR name LIKE ?) ORDER BY student_id",
            (q, f"%{q}%", f"%{q}%"),
        ).fetchall()
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "学生信息"
    sheet.append(["学号", "姓名", "年龄", "成绩"])
    for row in rows:
        sheet.append(list(row))
    for column in sheet.columns:
        sheet.column_dimensions[column[0].column_letter].width = 18
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=students.xlsx"},
    )


@app.post("/students/import")
async def import_students(request: Request, file: UploadFile = File(...), csrf_token: str = Form(...)):
    user = require_write_user(request)
    if not user or not valid_csrf(request, csrf_token):
        return RedirectResponse("/students", status_code=303)
    try:
        workbook = load_workbook(io.BytesIO(await file.read()), read_only=True, data_only=True)
        sheet = workbook.active
        headers = [str(cell.value or "").strip() for cell in next(sheet.iter_rows(max_row=1))]
        expected = ["学号", "姓名", "年龄", "成绩"]
        if headers[:4] != expected:
            raise ValueError("Excel第一行必须依次为：学号、姓名、年龄、成绩")
        imported = 0
        with connection() as conn:
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not any(value is not None and str(value).strip() for value in row[:4]):
                    continue
                values = parse_student(str(row[0] or ""), str(row[1] or ""), str(row[2] or ""), str(row[3] or ""))
                conn.execute(
                    "INSERT INTO students(student_id, name, age, score) VALUES (?, ?, ?, ?) ON CONFLICT(student_id) DO UPDATE SET name=excluded.name, age=excluded.age, score=excluded.score",
                    values,
                )
                imported += 1
            write_audit(conn, user["id"], "import_students", f"Excel导入 {imported} 条")
        request.session["message"] = f"成功导入 {imported} 条学生记录"
    except Exception as error:
        request.session["message"] = f"导入失败：{error}"
    return RedirectResponse("/students", status_code=303)


@app.get("/api/stats")
def stats(request: Request):
    if not require_user(request):
        return {"error": "未登录"}
    with connection() as conn:
        rows = conn.execute("SELECT score FROM students").fetchall()
    scores = [float(row["score"]) for row in rows]
    bands = [0, 0, 0, 0]
    for score in scores:
        bands[0 if score < 60 else 1 if score < 70 else 2 if score < 85 else 3] += 1
    return {
        "count": len(scores),
        "average": round(sum(scores) / len(scores), 2) if scores else 0,
        "highest": max(scores) if scores else 0,
        "lowest": min(scores) if scores else 0,
        "bands": bands,
    }


@app.get("/users", response_class=HTMLResponse)
def users(request: Request):
    user = require_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse("/dashboard", status_code=303)
    with connection() as conn:
        rows = conn.execute("SELECT id, username, full_name, role, is_active, created_at FROM users ORDER BY id").fetchall()
    return render(request, "users.html", title="用户与权限", users=rows)


@app.post("/users/{user_id}/role")
def update_role(user_id: int, request: Request, role: str = Form(...), csrf_token: str = Form(...)):
    user = require_user(request)
    if not user or user["role"] != "admin" or not valid_csrf(request, csrf_token):
        return RedirectResponse("/dashboard", status_code=303)
    if role not in {"admin", "teacher", "viewer"}:
        role = "viewer"
    with connection() as conn:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        write_audit(conn, user["id"], "update_role", f"用户 {user_id} 设置为 {role}")
    request.session["message"] = "权限更新成功"
    return RedirectResponse("/users", status_code=303)
