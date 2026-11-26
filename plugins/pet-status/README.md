# 状态查询插件 pet-status

## 它能干什么
一句话汇总桌宠当前状态：角色、心情、精力、主题、尺寸、跟随开关。供宿主同步或用户查询。

## 怎么测
```bash
echo '{"t":"hello"}' | python main.py
echo '{"t":"ask","intent":"status","args":{}}' | python main.py
echo '{"t":"ask","intent":"在干嘛","args":{}}' | python main.py
```

## 隐私设计（重要）
读桌宠 `config.json` 时**只挑非敏感字段**：theme / size_height / follow_activity / check_updates / character / terms_seen。

**`api_key`、`base_url`、`model` 一律不返回**——即使插件被调用，也不会把你的 API Key 泄露到气泡或日志里。

## 依赖
仅标准库。只读，不写任何文件。
