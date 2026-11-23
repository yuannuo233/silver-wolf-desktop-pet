# Silver Wolf Desktop Pet 银狼桌宠

> “Hack into your desktop.” —— 银狼钻进你的电脑里啦

A Silver Wolf inspired desktop companion for Windows: **a clean main app**
(sidebar + home/chat/settings) **plus a floating desktop pet**.
AI chat with any OpenAI-compatible API; standalone exe, or run from source
with just `Pillow` (`pip install -r requirements.txt`).

致敬《崩坏：星穹铁道》「银狼」的桌面伴侣（非官方粉丝作品，免费、非商业）：
**正经主程序窗口** + 桌面浮窗桌宠，双箭齐发。

## ✨ Features 功能

- 🖥️ **完整主界面**：侧边栏导航（主页 / 聊天 / 设置），自绘一体化标题栏（无系统白边），浅 / 深 / 赛博蓝三主题
- 🐺 **桌面浮窗宠物**：永远置顶、单击说话、双击快问快答、右键菜单（动作 / 尺寸 / 主题开关）
- 🏃 **拖拽 = 瞄准，松手 = 她自己跑过去**：按住拖动时窗口不动、她原地转身面朝方向，松手后以固定速度跑向落点，跑到停回待机
- 🎬 **11 组帧动画**：待机（含眨眼）/ 左右跑 / 转身过渡 / 挥手 / 打盹 / 伸懒腰 / 吃棒棒糖 / 敲键盘 / 玩掌机
- ⌨️ **跟着你做事**：你在编辑器里打字她跟着敲键盘，前台是游戏她掏掌机自己玩（右键可关）
- 💬 **AI 聊天**：任意 OpenAI 兼容接口——DeepSeek / 智谱 / 通义 / Kimi / 豆包方舟 / OpenAI / 本地 Ollama，预设一键填
- 🎭 **高度还原人设**：三档系统提示词（完整版 / 平衡版 / 省token版）自由编辑实时生效
- 📏 **尺寸五档**：迷你 100px → 特大 400px，记住偏好
- 📦 独立 exe（无需 Python）；源码仅依赖 Pillow

## 🚀 立即使用（无需编程 / No coding needed）

1. 前往 [Releases 页面](../../releases)（发布后可用；也可用简介里的备用下载）
2. 下载 `SilverWolfPet-v0.6.17-win64.zip`（或 Releases 里最新版本）
3. 解压，**双击 `SilverWolfPet.exe`**
4. 主界面弹出（主页 / 聊天 / 设置），同时银狼出现在屏幕右下角！

- ✅ 无需安装 Python，解压即用
- ✅ 系统：Windows 10 / 11（64 位）
- ✅ 双击桌宠桌面快捷方式也可直达
- ✅ 从源码跑也不会弹出黑控制台（只隐藏属于她自己的那个控制台）

> **首次运行弹蓝色警告「Windows 已保护你的电脑」？**
> 这是对未付费签名程序的统一提示。点 **更多信息 → 仍要运行** 即可。
> 杀毒软件误报同理，添加信任即可。程序完全开源，可自行审阅源码。
> 首次启动若"没反应"，多为安全软件在扫描新 exe（本机实测 30~45s），等一会儿或加信任后再开。

## 🤖 给 AI 助手 / Agent 的安装说明

如果你是被派来安装本项目的 AI 助手，直接照做即可：

```text
目标：安装银狼桌宠（SilverWolfPet）
步骤：
1. 下载最新 Release 的 zip：
   https://github.com/<YOUR_USERNAME>/silver-wolf-desktop-pet/releases/latest
   （资产名形如 SilverWolfPet-v0.6.17-win64.zip）
2. 解压 zip 到任意目录（如 C:\Tools\SilverWolfPet）
3. 运行 SilverWolfPet.exe；如遇 SmartScreen 蓝色警告，
   点击"更多信息"→"仍要运行"
4. 验证：弹出"银狼桌宠"主窗口 + 屏幕右下角出现 Q 版银狼即成功
5. 关闭主窗口 = 退出程序；桌宠右键菜单也有"退出程序"
6. 可选：在主窗口「设置」页填 AI 供应商 API Key 启用聊天
备选（机器已有 Python 3.9+ 时）：git clone 本仓库 → `pip install -r requirements.txt` → `python main.py`
```

## 💬 AI 聊天配置（可选，两分钟搞定）

不配置 AI 也完全可用（她说离线台词）。想跟她真聊，只需要一个 API 密钥：

1. 主界面 → **设置** 页（或桌宠右键 → 设置…）
2. 选**厂商预设**（推荐智谱 GLM 的 `glm-4-flash`：有免费额度）
3. 到该厂商官网注册并创建 API Key，粘贴进密钥框
4. 点 **保存** → 「聊天」页或双击桌宠开聊！

| 预设 | 接口地址 | 默认模型 | 备注 |
| --- | --- | --- | --- |
| DeepSeek | `https://api.deepseek.com/v1` | deepseek-chat | 便宜量大 |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | glm-4-flash | **有免费额度** |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | qwen-turbo | 阿里云 |
| Kimi | `https://api.moonshot.cn/v1` | moonshot-v1-8k | 长文本 |
| 豆包·火山方舟 | `https://ark.cn-beijing.volces.com/api/v3` | 填接入点 ID | 控制台创建接入点 |
| OpenAI | `https://api.openai.com/v1` | gpt-4o-mini | 国际 |
| Ollama 本地 | `http://127.0.0.1:11434/v1` | 本机模型名 | 完全免费、离线 |

- **人设提示词**：三档一键填入（完整版 / 平衡版 / 省token版），自由编辑；AI 每次回复都按这份"角色说明书"来演。
- **隐私**：API 密钥只保存在 `%APPDATA%\SilverWolfPet\config.json`，不经过任何第三方服务器。
- **记忆**：带最近 6 句对话上下文，不无限膨胀（省 token）。

## 🛠️ 从源码运行（开发者）

```bash
git clone https://github.com/<YOUR_USERNAME>/silver-wolf-desktop-pet.git
cd silver-wolf-desktop-pet
pip install -r requirements.txt   # 只有 Pillow 一个依赖
python main.py
```

- Windows 下也可以直接双击 `启动银狼桌宠.bat`（自动优先用 pythonw 无控制台启动）
- **VSCode 用户**：直接"打开文件夹"选本仓库 → 装推荐扩展（Python + 中文语言包）→
  按 **F5** 即运行（`.vscode/launch.json` 已配好）；注释全中文，`files.encoding=utf8` 已锁，不会乱码
- 帧动画 / 平滑缩放 / 图标处理都依赖 Pillow；缺失时程序仍能启动但退化为单帧浮动模式

### 打包成 exe（维护者参考）

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name SilverWolfPet --icon icon.ico ^
  --add-data "assets;assets" --add-data "icon.png;." main.py
```

（不要用 `--splash`：PyInstaller 闪屏在部分机器上会残留/挡住主窗口。）

## Replace the sprite 换成你自己的立绘

1. 准备一张 **透明背景 PNG**（推荐 chibi，高度 150–300px；大尺寸的存成 `silver_wolf_hd.png` 供缩放）
2. 覆盖 `assets/` 里的同名文件
3. 重新运行

背景不是透明的？用仓库自带的工具抠一下（需要 Pillow）：

```bash
python scripts/remove_background.py 你的图.png 输出.png 32
```

## Roadmap 路线图

- [x] v0.1 单帧立绘 + 浮动 + 台词气泡 + 拖拽 + 右键菜单
- [x] v0.2 AI 对话（OpenAI 兼容全通吃）+ 尺寸五档 + 三档可编辑人设提示词
- [x] v0.3 主程序界面（主页/聊天/设置）+ 双击聊天 + 桌宠与主界面联动
- [x] v0.4 多状态动画状态机（frames.json 规格）
- [x] v0.6 H3 素材帧动画全面接管：待机眨眼 / 跑动 / 转身过渡 / 右键动作 / 敲键盘 / 玩掌机
- [x] v0.6.13+ 自绘一体化标题栏 + 三主题 + 跟着你做事
- [x] v0.6.17 任务栏图标/按钮 + 黑控制台自隐藏 + 窗口轮廓
- [ ] 多角色皮肤

## Disclaimer 免责声明

**完整法律声明见 [DISCLAIMER.md](DISCLAIMER.md)（中英双语）。** 要点：

- **非官方粉丝作品（Unofficial fan work）**，与 miHoYo / HoYoverse / COGNOSPHERE 无关，也未经其授权或认可。
- 未使用任何游戏拆包素材（立绘、语音、UI 图标），台词与提示词为原创，Q 版形象为粉丝向原创/AI 辅助二创。
- 代码 MIT 开源，但**不包含**任何对米哈游角色形象 / 名称 / 商标的授权；禁止商业用途。
- AI 回复由第三方大模型生成，不代表官方设定；API 密钥只存本机，请自行保管。
- 本项目完全免费、非商业用途；如权利方提出合理要求将配合修改或下架相关素材。

## License

[MIT](LICENSE)
