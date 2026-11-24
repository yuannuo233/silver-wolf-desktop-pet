"""示例插件：报时。

这是写给插件作者看的模板。它只做三件事：
  1. 从 stdin 读一行 JSON
  2. 看看是不是自己能处理的 intent
  3. 往 stdout 写一行 JSON 回答

注意：stdout 只能输出 JSON！一句多余的 print 都会让宿主解析失败。
调试信息请写到 stderr（sys.stderr.write）。
"""
import datetime
import json
import sys

WEEK = ["一", "二", "三", "四", "五", "六", "日"]


def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True,
                "intents": ["clock", "time"],
                "description": "告诉她现在几点"}

    if t == "ask":
        intent = msg.get("intent")
        if intent not in ("clock", "time"):
            return {"t": "reply", "ok": False, "error": "这个 intent 我不处理: %s" % intent}
        now = datetime.datetime.now()
        return {
            "t": "reply",
            "ok": True,
            "text": "现在是 %d 点 %02d 分，星期%s。" % (
                now.hour, now.minute, WEEK[now.weekday()]),
        }

    return {"t": "reply", "ok": False, "error": "不认识的消息类型: %s" % t}


def main():
    line = sys.stdin.readline()
    if not line.strip():
        print(json.dumps({"t": "reply", "ok": False, "error": "没有输入"},
                         ensure_ascii=False))
        return
    try:
        msg = json.loads(line)
        reply = handle(msg)
    except Exception as e:
        reply = {"t": "reply", "ok": False, "error": "插件内部错误: %s" % e}
    print(json.dumps(reply, ensure_ascii=False))


if __name__ == "__main__":
    main()
