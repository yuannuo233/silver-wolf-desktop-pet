# 天气插件 weather

## 它能干什么
查当前天气（温度、体感、湿度、风速、天气描述），可选未来 1~7 天预报。用 Open-Meteo 免费 API，**不需要 API key**。

## 怎么测
```bash
echo '{"t":"hello"}' | python main.py
echo '{"t":"ask","intent":"weather","args":{"city":"北京"}}' | python main.py
echo '{"t":"ask","intent":"weather","args":{"city":"上海","forecast_days":3}}' | python main.py
```

## 意图与参数
| intent | 参数 | 说明 |
| --- | --- | --- |
| weather / 天气 / 气温 / forecast | `city`：中文城市名（内置 20 个常用城市，其他走地理编码） | 二选一 |
| | `latitude` + `longitude`：经纬度 | 二选一 |
| | `forecast_days`：1~7，默认 1 | 可选 |

## 依赖
仅标准库 `urllib`。**不需要 requests**。需要联网。

## 装到桌宠
整个 `weather/` 文件夹拷进桌宠 `plugins/`，重启桌宠，在「插件」页启用。
