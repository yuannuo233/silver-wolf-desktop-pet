"""插件：天气（和风天气 API）。

给插件作者的话：
  这是"真实可用"的模板。和你朋友的报时插件结构一模一样，
  只是把 datetime.now() 换成了联网请求。

用前要做的两件事（写在 插件开发说明.md 里）：
  1. 去 qweather.com 注册，拿一个 API Key（免费）
  2. 把下面的 KEY 和 CITY 换成你自己的

Key 和城市也可以从环境变量读，避免写死在代码里：
  QWEATHER_KEY  QWEATHER_CITY
"""
import json
import os
import sys
import urllib.request

# 换成你自己的。留空时从环境变量读。
KEY = os.environ.get("QWEATHER_KEY", "")
CITY = os.environ.get("QWEATHER_CITY", "101010100")   # 101010100 = 北京

# 免费版是 devapi.qweather.com；如果用的是付费订阅换成 api.qweather.com
BASE = "https://devapi.qweather.com/v7"


def get_json(url):
    with urllib.request.urlopen(url, timeout=8) as r:
        return json.loads(r.read().decode("utf-8"))


def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True, "intents": ["weather"],
                "description": "播报今天的天气"}

    if t == "ask":
        if msg.get("intent") != "weather":
            return {"t": "reply", "ok": False, "error": "我只处理 weather"}
        if not KEY:
            return {"t": "reply", "ok": False,
                    "error": "还没配置和风天气的 KEY，见 插件开发说明.md"}

        # 先查实时天气
        url = "%s/weather/now?location=%s&key=%s" % (BASE, CITY, KEY)
        try:
            data = get_json(url)
        except Exception as e:
            return {"t": "reply", "ok": False, "error": "联网失败: %s" % e}
        if data.get("code") != "200":
            return {"t": "reply", "ok": False,
                    "error": "天气接口返回 %s：%s" % (data.get("code"),
                             data.get("code", ""))}

        now = data.get("now", {})
        text = "现在%s，%s度，%s风%s级。" % (
            now.get("text", "天气未知"), now.get("temp", "?"),
            now.get("windDir", ""), now.get("windScale", "?"))
        return {"t": "reply", "ok": True, "text": text}

    return {"t": "reply", "ok": False, "error": "不认识的消息类型: %s" % t}


def main():
    line = sys.stdin.readline()
    if not line.strip():
        print(json.dumps({"t": "reply", "ok": False, "error": "没有输入"},
                         ensure_ascii=False))
        return
    try:
        reply = handle(json.loads(line))
    except Exception as e:
        reply = {"t": "reply", "ok": False, "error": "插件内部错误: %s" % e}
    print(json.dumps(reply, ensure_ascii=False))


if __name__ == "__main__":
    main()
