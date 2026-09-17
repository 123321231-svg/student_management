import requests


def test_api():

    url = "https://httpbin.org/get"

    try:

        response = requests.get(
            url,
            timeout=5
        )

        print("\n========== HTTP/API测试 ==========")

        print(
            "HTTP状态码：",
            response.status_code
        )

        if response.status_code == 200:

            print("请求成功！")

            data = response.json()

            print("\n服务器返回的数据：")
            print(data)

        else:

            print("请求失败")

    except requests.RequestException as e:

        print("HTTP请求发生错误：", e)

