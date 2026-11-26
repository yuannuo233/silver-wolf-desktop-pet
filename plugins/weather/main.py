"""天气插件：Open-Meteo 免费 API，无需 key。仅标准库 urllib。"""
import json, os, sys, urllib.parse, urllib.request

INTENTS = ["weather", "天气", "气温", "forecast"]
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 12

CITY_COORDS = {
    "北京": (39.9042, 116.4074), "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644), "深圳": (22.5431, 114.0579),
    "杭州": (30.2741, 120.1551), "成都": (30.5728, 104.0668),
    "重庆": (29.5630, 106.5516), "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398), "南京": (32.0603, 118.7969),
    "天津": (39.3434, 117.3614), "苏州": (31.2989, 120.5853),
    "长沙": (28.2282, 112.9388), "郑州": (34.7466, 113.6254),
    "青岛": (36.0671, 120.3826), "厦门": (24.4798, 118.0894),
    "昆明": (25.0389, 102.7183), "哈尔滨": (45.8038, 126.5349),
    "香港": (22.3193, 114.1694), "台北": (25.0330, 121.5654),
}
WMO = {0:"晴",1:"大部晴朗",2:"局部多云",3:"阴",45:"雾",48:"雾凇",
       51:"小毛毛雨",53:"毛毛雨",55:"大毛毛雨",56:"冻毛毛雨",57:"强冻毛毛雨",
       61:"小雨",63:"中雨",65:"大雨",66:"冻雨",67:"强冻雨",71:"小雪",73:"中雪",
       75:"大雪",77:"雪粒",80:"小阵雨",81:"中阵雨",82:"强阵雨",85:"小阵雪",
       86:"强阵雪",95:"雷暴",96:"雷暴伴小冰雹",99:"雷暴伴大冰雹"}

def _get_json(url, params):
    full = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full, headers={"User-Agent": "SilverWolfPet-WeatherPlugin/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _resolve(city):
    key = (city or "").strip()
    if key in CITY_COORDS:
        return CITY_COORDS[key][0], CITY_COORDS[key][1], key
    if key.endswith("市") and key[:-1] in CITY_COORDS:
        k = key[:-1]
        return CITY_COORDS[k][0], CITY_COORDS[k][1], k
    data = _get_json(GEO_URL, {"name": key, "count": 1, "language": "zh"})
    results = data.get("results") or []
    if results:
        r = results[0]
        return float(r["latitude"]), float(r["longitude"]), r.get("name", key)
    return None

def _weather(city, lat, lon, days):
    if not city and (lat is None or lon is None):
        return {"ok": False, "error": "请给 city 或 latitude + longitude"}
    label = city or f"{lat},{lon}"
    tz = "auto"
    if city:
        coord = _resolve(city)
        if not coord:
            return {"ok": False, "error": f"没找到这个城市：{city}，试试经纬度"}
        lat, lon, label = coord
    params = {"latitude": lat, "longitude": lon, "timezone": tz,
              "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"}
    if days > 1:
        params["daily"] = "weather_code,temperature_2m_max,temperature_2m_min"
        params["forecast_days"] = min(max(days, 1), 7)
    data = _get_json(FORECAST_URL, params)
    cur = data.get("current", {})
    code = cur.get("weather_code")
    desc = WMO.get(code, f"未知({code})")
    bits = [f"{label}：{desc}", f"温度 {cur.get('temperature_2m')}°C"]
    if cur.get("apparent_temperature") is not None:
        bits.append(f"体感 {cur.get('apparent_temperature')}°C")
    if cur.get("relative_humidity_2m") is not None:
        bits.append(f"湿度 {cur.get('relative_humidity_2m')}%")
    if cur.get("wind_speed_10m") is not None:
        bits.append(f"风速 {cur.get('wind_speed_10m')} km/h")
    out = {"ok": True, "text": "，".join(bits), "location": label,
           "temperature_c": cur.get("temperature_2m"), "weather": desc,
           "weather_code": code, "timezone": data.get("timezone")}
    if days > 1 and "daily" in data:
        d = data["daily"]
        out["forecast"] = [{"date": d["time"][i], "weather": WMO.get(d["weather_code"][i], "未知"),
                            "max_c": d["temperature_2m_max"][i], "min_c": d["temperature_2m_min"][i]}
                           for i in range(len(d.get("time", [])))]
    return out

def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True, "intents": INTENTS,
                "description": "查天气，中文城市名或经纬度，免 API key"}
    if t != "ask":
        return {"t": "reply", "ok": False, "error": "未知消息类型"}
    intent = msg.get("intent", "")
    if intent not in INTENTS:
        return {"t": "reply", "ok": False, "error": "不支持的意图：" + str(intent)}
    args = msg.get("args") or {}
    city = args.get("city")
    if not city:
        txt = str(args.get("text") or args.get("query") or args.get("action") or "")
        for name in CITY_COORDS:
            if name in txt:
                city = name
                break
        if not city:
            city = os.environ.get("WEATHER_DEFAULT_CITY") or "北京"
    try:
        result = _weather(city, args.get("latitude"), args.get("longitude"),
                          int(args.get("forecast_days") or 1))
        if not result.get("ok"):
            return {"t": "reply", "ok": False, "error": result.get("error")}
        return {"t": "reply", "ok": True, **result}
    except Exception as exc:
        return {"t": "reply", "ok": True, "text": "联网查天气失败，可能是网络不通：" + str(exc)[:60],
                "degraded": True}

if __name__ == "__main__":
    try:
        line = sys.stdin.readline()
        msg = json.loads(line) if line.strip() else {}
        reply = handle(msg)
    except Exception as exc:
        reply = {"t": "reply", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
