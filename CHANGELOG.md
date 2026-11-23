# Changelog 更新日志

All notable changes will be recorded here. 所有更新都会记录在这里。

## 0.6.17 (2026-11-23)

- 修复：拖拽时"原地踏步"的观感。**拖拽仍然是"只瞄准"**（窗口一动不动、她原地转身面朝拖拽方向），松手后她以 `320px/s` 自己的速度跑向你松手的位置，跑到停回待机 —— 保持你验收过的这套手感，只把松手后的落点算得更准
- 修复：点最小化后窗口从任务栏消失。原来用 `withdraw()` 把窗口摘掉，Windows 连任务栏条目一起撤。改用 `SW_MINIMIZE`，窗口保持图标化但不摘除，**任务栏按钮一直在，点一下就能还原**；「打开主界面」也补了 `SW_RESTORE`
- 修复：任务栏图标是 Python 的 logo。根因是进程就是 `python.exe`，Windows 按 exe 身份给任务栏按钮配图标。新增 `SetCurrentProcessExplicitAppUserModelID`，并给 `ICON_BIG / ICON_SMALL / ICON_SMALL2` 三个槽位都发 `WM_SETICON`，任务栏和 Alt-Tab 都是银狼
- 修复：启动时旁边那个黑控制台窗口。新增 `hide_own_console()`：只有挂在这个控制台上的进程全是 Python 启动器时才隐藏（用户自己的 cmd / PowerShell / Windows Terminal 不会被误藏）
- 新增：窗口外轮廓。浅色主题下纯白无边框窗口在白桌面上没有边界，现在用两层 1px 边框（`edge` + `edge_in`）框出窗口，三套主题各有配色
- 调整：等待 AI 回复时的气泡台词从"让我黑进服务器看看"改为"嗯……等我想一下"
- 打包：spec 补 `icon.ico`（之前的 exe 里没有它，`set_window_icon` 取不到文件）；仓库清掉 `__pycache__` 与 `assets/stand/preview_*.gif`（开发期核对图，程序不引用）

## 0.6.16 (2026-11-23)

- 修复：打字时不敲键盘。原来只有编辑器/终端白名单里的进程才算"在打字"，在豆包客户端等任意应用里打字都被忽略。改为：**任何应用里按键盘都触发 typing，只有桌面/资源管理器除外，游戏优先走 console**
- 新增低级键盘钩子（`WH_KEYBOARD_LL`），只记录最后一次按键时间，能区分"按键盘"和"只滑鼠标"；装不上自动降级
- 拖拽手感：按住不动时她改为**慢速小碎步原地倒腾**（不再无限全速空跑），手一动立刻提速
- 代码清理：删除 `EDITOR_EXES` 白名单等死代码，修 `settings.py` 里 `except` 变量被 `del` 后延迟调用导致的 `NameError`（表现为"测试接口失败时界面毫无反应"），pyflakes 零告警
- 源码注释全部改为英文（公开仓库只留代码与英文注释，中文注释版单独在本地保留，不随仓库发布）

## 0.6.15 (2026-11-23)

- 拖拽重做：拖拽时窗口不再跟鼠标飞（转身过渡不再"滑步"），松手后银狼以自己的速度（320px/s）跑向鼠标落点，跑到停回待机；跑途中再抓住可取消
- 移除 v0.6.13 的"量子传送"（用户验收：很怪）
- 抠图回退到原版规则：补洞规则会误删个别帧眼白，用户拍板保留原样（眼白完整性优先）
- 主界面左下角版本号与"非官方粉丝作品"之间加空行，避免误读为官方版本
- 新增 `DISCLAIMER.md` 中英双语法律声明、`requirements.txt`（Pillow）；README 全面更新
- 清理仓库内开发期临时脚本；.gitignore 补虚拟环境/打包产物/系统垃圾文件
- 修复：无 Pillow 降级模式下松手落点直接落位；自动驾驶期间被右键动作抢状态时不留僵尸目标；双击聊天取消自动驾驶

## 0.6.14 (2026-11-23)

- 热修：v0.6.13 补洞规则误删眼白（眼白是实心月牙不是环），改用"与逐帧外背景基准色偏差≤8"判别；个别帧仍误删，于 0.6.15 整体回退

## 0.6.13 (2026-11-23)

- 修复"松手后原地还在跑"：拖拽事件改绑整个 canvas + Motion 丢左键位兜底补松手
- 修复待机不眨眼：idle 手工锁 4~31 帧全取 28 帧（含两次闭眼），100ms/帧
- 主窗口去系统标题栏：自绘 TitleBar（图标+标题+版本+最小化/关闭+拖窗），无边框窗口键盘焦点修复（AttachThreadInput）
- 新增 typing / console 状态与前台进程触发逻辑（编辑器打字→敲键盘；游戏→玩掌机），右键"跟着我做事"开关
- 新增量子传送（0.6.15 移除）；表情贴纸功能应用户要求取消
- 修复首次双击聊天 AttributeError（chat_win 未初始化）

## 0.4.0 (2026-11-21)

- 新增多帧动画状态机：待机（呼吸/前倾/眨眼循环）、被拖拽时按方向播放左右跑步循环、拎住不动时挣扎
- 动画由"部件拼装"生成：角色拆成 14 个零件（头/躯干/大小臂/大小腿/脚），程序按骨骼层级驱动，头身比永远一致
- 新增 assets/stand/frames.json 动画规格（与豆包协作的帧描述格式）
- 拖拽方向自动切换跑步朝向，松手回待机
- Add a multi-state frame animation engine (idle / drag / run left / run right) driven by parts-assembled frames.

## 0.3.2 (2026-11-21)

- 主界面全面改版：浅色卡片风（白卡片 + 紫强调 + 扁平按钮 + 悬停反馈）
- 主页横幅换为正常比例官方画风立绘（非 Q 版）
- 修复：PyInstaller 启动画面不再残留（打开主窗口即自动关闭）
- 修复：主窗口启动即弹到最前
- 快聊卡片去系统标题栏：自绘暗色头栏（可拖动 + ✕ 关闭）
- 设置页浅色化，输入框/按钮统一扁平风
- Main UI redesign to a light card theme, normal-proportion banner art, splash auto-close fix, and various UX polish.

## 0.3.0 (2026-11-21)

- 新增主程序界面：侧边栏导航（主页 / 聊天 / 设置），双击 exe 打开完整应用，桌宠作为置顶随从同时出现
- 新增聊天页：完整聊天记录（彩色角色标记）+ 输入框，与桌宠气泡实时同步
- 新增主页横幅与状态灯（AI 已就绪 / 未配置一目了然）
- 桌宠改为子窗口架构：菜单新增"打开主界面 / 隐藏桌宠"，关闭主窗口即退出
- 图标重制：ComfyUI 生成银狼特征头像（护目镜 + 蝴蝶结 + 毛领），exe 图标 / 主界面 / 快捷方式全套换装
- 启动体验：双击立即显示启动画面（splash），就位后自动打招呼
- Add a full main window UI (home/chat/settings), chat log page, banner, new identity-accurate icon, and a splash screen.

## 0.2.0 (2026-11-21)

- 新增 AI 聊天：支持任意 OpenAI 兼容接口，设置窗口内置厂商预设（DeepSeek / 智谱 / 通义 / Kimi / 豆包方舟 / OpenAI / Ollama 本地）
- 新增人设提示词系统：完整版 / 平衡版 / 省token版 一键填入，可自由编辑
- 新增尺寸调节：迷你 100px / 小 140px / 标准 200px / 大 280px / 特大 400px，右键切换并记住偏好
- 新增聊天窗（双击银狼打开）与短期记忆（最近 6 句）
- 首次提供打包版 SilverWolfPet.exe（无需 Python，解压即用）：双击立即显示启动画面，就位后自动打招呼
- Add AI chat via any OpenAI-compatible endpoint, editable persona prompts (3 presets), sprite size presets, and a standalone Windows build.

## 0.1.0 (2026-11-21)

- 首个版本：单帧立绘 + 上下浮动 + 台词气泡 + 拖拽 + 右键菜单。
- Initial release with sprite, idle bobbing, speech bubbles, dragging and context menu.
