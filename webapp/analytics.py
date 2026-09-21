"""Pandas-based academic analytics kept independent from HTTP routes."""

import pandas as pd


def build_student_trend(records: list[dict]) -> dict:
    if not records:
        return {"labels": [], "scores": [], "direction": "stable", "change": 0, "risk_reasons": []}

    frame = pd.DataFrame(records).sort_values(["exam_date", "assessment_id"])
    scores = frame["score"].astype(float).tolist()
    change = round(scores[-1] - scores[0], 2) if len(scores) > 1 else 0
    direction = "up" if change > 0 else "down" if change < 0 else "stable"
    risk_reasons: list[str] = []
    if int((frame["score"] < 60).sum()) >= 2:
        risk_reasons.append("连续不及格")
    if len(scores) >= 2 and all(right < left for left, right in zip(scores, scores[1:], strict=False)):
        risk_reasons.append("成绩连续下降")

    return {
        "labels": frame["assessment_name"].tolist(),
        "scores": scores,
        "direction": direction,
        "change": change,
        "risk_reasons": risk_reasons,
    }


def build_data_quality(students: list[dict], scores: list[dict]) -> dict:
    student_frame = pd.DataFrame(students)
    score_frame = pd.DataFrame(scores)
    if student_frame.empty:
        missing_email_count = 0
        active_student_ids: set[int] = set()
    else:
        email = student_frame["email"].fillna("").astype(str).str.strip()
        missing_email_count = int((email == "").sum())
        active_student_ids = set(student_frame["id"].astype(int).tolist())

    orphan_score_count = 0
    if not score_frame.empty:
        orphan_score_count = int((~score_frame["student_id"].astype(int).isin(active_student_ids)).sum())

    return {
        "student_count": len(students),
        "missing_email_count": missing_email_count,
        "orphan_score_count": orphan_score_count,
    }
