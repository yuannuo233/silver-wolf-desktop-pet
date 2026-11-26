# 截屏插件 screen

## 它能干什么
截取主屏幕存成 PNG，返回路径、尺寸、字节数。可选 OCR 文字识别（需装 Tesseract）。

## 怎么测
```bash
echo '{"t":"hello"}' | python main.py
echo '{"t":"ask","intent":"screenshot","args":{}}' | python main.py
echo '{"t":"ask","intent":"ocr","args":{"lang":"chi_sim"}}' | python main.py
```

## 意图与参数
| intent | 参数 | 说明 |
| --- | --- | --- |
| screenshot / 截图 / 截屏 | `out_dir`（可选）、`filename`（可选） | 截屏存 PNG |
| ocr / 屏幕 | 上面 + `lang`（默认 eng，中文用 chi_sim） | 截屏后识别文字 |

## 依赖（可选，缺了不会崩）
```bash
pip install mss pillow           # 截屏（推荐）
pip install pytesseract          # OCR（还需另装 Tesseract 引擎并加进 PATH）
```
未装依赖时返回明确提示，不会让插件报错。

## 隐私
截图只存本机 `%APPDATA%\SilverWolfPet\plugins\screen\screenshots\`，不上传。

## 装到桌宠
整个 `screen/` 文件夹拷进桌宠 `plugins/`，重启桌宠，在「插件」页启用。
