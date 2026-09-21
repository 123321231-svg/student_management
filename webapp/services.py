"""可独立测试的业务规则。

路由层只负责接收 HTTP 输入；这里负责校验和计算，方便在网页、API、
命令行工具与未来的 EXE 版本之间复用。
"""


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


def build_score_stats(scores: list[float]) -> dict:
    bands = [0, 0, 0, 0]
    for score in scores:
        bands[0 if score < 60 else 1 if score < 70 else 2 if score < 85 else 3] += 1
    count = len(scores)
    return {
        "count": count,
        "average": round(sum(scores) / count, 2) if count else 0,
        "highest": max(scores) if scores else 0,
        "lowest": min(scores) if scores else 0,
        "pass_rate": round(sum(score >= 60 for score in scores) / count * 100, 1) if count else 0,
        "excellent_rate": round(sum(score >= 85 for score in scores) / count * 100, 1) if count else 0,
        "bands": bands,
    }
