import pandas as pd


def data_analysis(conn):

    df = pd.read_sql_query(
        "SELECT * FROM students",
        conn
    )

    if df.empty:
        print("\n暂无学生数据")
        return

    print("\n========== 数据分析 ==========")

    print("\n学生数量：")
    print(len(df))

    print("\n平均成绩：")
    print(round(df["score"].mean(), 2))

    print("\n最高成绩：")
    print(df["score"].max())

    print("\n最低成绩：")
    print(df["score"].min())

    print("\n========== 成绩排行榜 ==========")

    ranking = df.sort_values(
        by="score",
        ascending=False
    )

    print(
        ranking[
            ["student_id", "name", "score"]
        ].to_string(index=False)
    )
