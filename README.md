# Sherlock GUI · 用户名检索工具（图形界面版）

把 [sherlock-project/sherlock](https://github.com/sherlock-project/sherlock) 的命令行操作变成可视化桌面应用。基于上游官方引擎，内置 481 个站点的 `data.json`，**站点列表随程序分发、离线可用**，运行时不会去 GitHub 拉取站点清单。

> 仅用于检索公开可访问的账号页面，请遵守法律法规与平台条款，不得用于骚扰、人肉搜索或侵犯他人隐私。

## 功能页面

| 页面 | 功能 |
| --- | --- |
| 🔍 **查询** | 输入一个或多个用户名、按站点筛选（留空即全部 481 个站点）、设置超时与代理、包含 NSFW 站点开关；开始 / 停止、实时进度条 |
| 📊 **结果** | 表格展示用户名 / 站点 / 状态 / URL / 耗时，命中行高亮，只看命中过滤，双击或按钮打开链接，导出 TXT / CSV / Excel |
| 📝 **日志** | 实时运行日志，可清空、保存为 txt |
| ⚙️ **设置** | 浅色 / 深色主题、字号、默认超时、默认代理、窗口置顶，一键保存或恢复默认，窗口大小自动记忆 |
| ℹ️ **关于** | 版本、内置站点数、官方仓库入口、文件说明与免责声明 |

其它特性：后台线程执行查询不卡界面、自定义 EXE 图标、无控制台黑窗口（`.pyw` / `-w`）、高 DPI 适配、配置自动保存。

## 文件说明

```
Sherlock_GUI/
├── gui.py / gui.pyw          主程序（内容相同；.pyw 双击无黑窗口）
├── app.ico                   程序 / EXE 图标
├── sherlock_core.py          业务封装：站点加载、查询、导出、自检
├── sherlock_project/         上游官方引擎 + resources/data.json（与 gui 同目录，勿删）
├── pyproject.toml            版本信息（勿删）
├── main.py                   原命令行入口（等价官方 sherlock CLI）
├── .venv/                    本机自带运行环境（Python 3.12 + tkinter + 依赖）
│
│  ── 配置（首次运行自动生成）──
├── config.json               界面配置（见 config.example.json）
│
│  ── 启动 / 打包脚本 ──
├── 启动.bat / 静默启动.vbs
├── 安装依赖.bat
├── 打包成EXE.bat
├── requirements.txt
├── README.md
└── dist/Sherlock_GUI.exe     打包产物（单文件，可直接双击分发）
```

## 快速开始

### 0. 从 GitHub 获取

```bash
git clone https://github.com/goodFLY88/Sherlock_GUI.git
cd Sherlock_GUI
```

仓库只含源码（不含 `.venv` 与 `dist` 产物）。克隆后先双击 `安装依赖.bat` 安装依赖，或下载 Release 中的 `Sherlock_GUI.exe` 直接运行。

### 1. 安装依赖

本机成品包自带 `.venv`（Python 3.12，含 tkinter 与全部依赖），**双击 `启动.bat` / `gui.pyw` 即可运行，无需另装 Python**。

分发到其它机器：推荐直接发送 `dist\Sherlock_GUI.exe`（单文件，无需 Python）；若发送源码包，目标机器装好 Python 3.10+ 后双击 `安装依赖.bat`，再运行 `gui.pyw`。

### 2. 运行

- 双击 `gui.pyw`（推荐，无黑窗口），或 `python gui.py`（调试，带控制台日志）
- 也可双击 `启动.bat` 或 `静默启动.vbs`
- 命令行自检：`python gui.py --selftest`（结果写入 `%TEMP%\sherlock_gui_selftest.json`）

### 3. 打包成 EXE

双击 `打包成EXE.bat`，或手动执行：

```bash
python -m PyInstaller -F -w --icon "app.ico" --name "Sherlock_GUI" ^
  --add-data "app.ico;." ^
  --add-data "pyproject.toml;." ^
  --add-data "pyproject.toml;sherlock_project" ^
  --add-data "sherlock_project\resources\data.json;sherlock_project\resources" ^
  --add-data "sherlock_project\resources\data.schema.json;sherlock_project\resources" ^
  --collect-data certifi --exclude-module tomli gui.py
```

- `-F` 单文件　`-w` 无控制台黑窗口　`--icon` 自定义图标　`--add-data` 把站点数据与图标打进 exe
- `pyproject.toml` 打两份，是因为 PyInstaller 会重定位 `__file__`，版本读取需要多路径兜底
- `--exclude-module tomli`：上游原本用第三方 `tomli` 读版本，其 mypyc 编译扩展在单文件包里无法加载；本成品的 `sherlock_project/__init__.py` 已改为优先使用 Python 3.11+ 内置的 `tomllib`
- 生成位置：`dist\Sherlock_GUI.exe`，可单独拷到任意 Windows 机器运行（无需 Python）

### 4. 命令行用法（可选）

```bash
python main.py --local octocat
python main.py --local --site GitHub --site Gitee user1 user2 --csv
```

## 配置说明

界面设置在「设置」页调整后自动保存到 `config.json`；删除该文件即恢复默认。可直接参考 `config.example.json`：

| 字段 | 说明 |
| --- | --- |
| `theme` | `light` / `dark` |
| `timeout` | 默认查询超时（秒） |
| `proxy` | 默认代理，例如 `http://127.0.0.1:7890` 或 `socks5://127.0.0.1:1080` |
| `include_nsfw` | 是否包含 NSFW 站点 |
| `show_all` | 结果表格是否显示未命中项 |
| `topmost` / `font_size` / `geometry` | 窗口置顶 / 字号 / 窗口大小 |

## 常见问题

- **大量站点超时**：境外站点受网络环境影响，可在「查询」页填代理，或先用「站点筛选」只测少数站点。
- **双击没反应 / 黑屏**：改用 `python gui.py` 查看控制台报错；确认已执行 `安装依赖.bat`。
- **打包后打不开**：确认 `app.ico`、`pyproject.toml`、`sherlock_project/resources/data.json` 都在同目录；用 `Sherlock_GUI.exe --selftest` 做无界面自检（结果写 `%TEMP%\sherlock_gui_selftest.json`）。
- **提示 `No module named '...__mypyc'`**：这是 `tomli` 编译扩展的问题；本成品已改用内置 `tomllib` 并在打包脚本中排除 `tomli`，重新双击 `打包成EXE.bat` 即可。
- **打包后读不到版本 / 找不到 pyproject.toml**：确保打包命令里有两个 `--add-data "pyproject.toml;..."`；本地 `get_version()` 已做多路径查找与兜底。
- **误报（显示已找到但页面不存在）**：Sherlock 基于 HTTP 状态/页面特征判定，个别站点可能变化，建议人工复核链接。

## 更新上游源码之后

站点数据或引擎有更新时，从 `..\sherlock` 的 git 仓库重新复制 `sherlock_project/resources/` 与 `pyproject.toml` 到本目录，再双击 `打包成EXE.bat` 重新打包即可。

⚠️ 请**保留本目录里适配过的 `sherlock_project/__init__.py`**（改用 stdlib `tomllib`、版本多路径兜底），不要整个目录覆盖，否则打包版会再次出现 `tomli` 的 mypyc 报错。EXE 是源码快照，不会随上游自动更新。
