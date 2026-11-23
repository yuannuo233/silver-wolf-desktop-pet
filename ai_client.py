"""Minimal chat client for OpenAI-compatible APIs (stdlib only).

Works with DeepSeek / Zhipu GLM / Qwen(DashScope) / Kimi / Doubao(Ark) /
OpenAI / Ollama ... — anything that speaks the /v1/chat/completions shape.
"""

import json
import urllib.error
import urllib.request

DEFAULT_TIMEOUT = 30


class AIError(Exception):
    """Friendly error wrapper shown in the speech bubble."""


def chat(
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_text: str,
    history=None,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Send one chat turn and return the assistant's reply text.

    history is a list of (role, content) tuples, the last few turns used as
    short-term memory.
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages += [{"role": role, "content": content} for role, content in (history or [])]
    messages.append({"role": "user", "content": user_text})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.9,   # a bit of randomness keeps her playful
        "max_tokens": 150,    # persona rules keep replies short anyway
        "stream": False,
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:180]
        raise AIError(f"接口报错 {e.code}：{detail}")
    except Exception as e:  # network down, timeout, DNS ...
        raise AIError(f"连不上接口：{e}")

    try:
        reply = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        raise AIError("返回格式不对：" + json.dumps(data, ensure_ascii=False)[:180])
    if not reply:
        raise AIError("模型返回了空回复，换个模型或再试一次")
    return reply
