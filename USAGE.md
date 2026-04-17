# social-auto-upload 使用指南

面向日常使用的快速说明。安装细节见 [docs/install.md](docs/install.md)，CLI 参数细节见 [docs/CLI.md](docs/CLI.md)。

---

## 1. 适用场景

- **CLI 主线（推荐）**：抖音、快手、小红书、Bilibili 的视频/图文上传、定时发布。
- **本地网页控制台（可选）**：装好 Web 依赖后运行 `sau-web`，用浏览器点点完成登录检查、上传视频/图文（默认只监听本机 `127.0.0.1:5050`）。**B 站登录**仍建议在终端执行 `sau bilibili login`（与官方 CLI 说明一致）。
- **其他平台**：视频号、百家号、TikTok 等通过 `examples/` 下脚本调用 uploader（见第 8 节）。

### 本地网页控制台（无代码基础用户）

```bash
uv pip install -e ".[web]"
sau-web
```

浏览器打开终端里提示的地址（一般为 `http://127.0.0.1:5050/`）。勿将端口映射到公网；上传大视频时请耐心等待请求结束。

---

## 2. 环境自检（装好后做一次）

在项目根目录、已激活虚拟环境中执行：

```bash
sau --help
sau douyin --help
```

若提示找不到 `sau`：

```bash
uv pip install -e .
```

浏览器驱动（**patchright 的 Chromium**）若未安装，在 **Windows PowerShell** 中（国内镜像）：

```powershell
$env:PLAYWRIGHT_DOWNLOAD_HOST="https://npmmirror.com/mirrors/playwright"; patchright install chromium
```

---

## 3. 配置文件 `conf.py`

可从 `conf.example.py` 复制为 `conf.py`（若仓库提供）。常用项：

| 项 | 含义 |
| --- | --- |
| `LOCAL_CHROME_PATH` | 可选，指定本机 Chrome 路径，例如 `C:/Program Files/Google/Chrome/Application/chrome.exe` |
| `LOCAL_CHROME_HEADLESS` | 无头浏览器默认行为（与 CLI 的 `--headed` / `--headless` 可配合理解） |
| `DEBUG_MODE` | 调试相关默认开关 |
| `XHS_SERVER` | 与小红书旧流程相关，多数 CLI 用户可忽略 |

---

## 4. 账号别名 `--account`

`--account` 后的名字是**你自己起的别名**，用于区分多账号、对应本地登录态；**不是**平台昵称。同一账号请固定使用同一个别名，例如 `my_dy_main`。

---

## 5. 通用流程（每个平台）

1. **登录**（首次或失效时）：`sau <平台> login --account <别名>`
2. **校验**：`sau <平台> check --account <别名>`
3. **上传**：`upload-video` 或 `upload-note`

登录过程中若生成二维码图片，用系统打开该图片扫码；**Bilibili** 若终端二维码显示不全，可看项目目录下的 `qrcode.png`。

---

## 6. 四平台 CLI 速查

以下路径请换成你的视频/图片绝对路径或相对项目根的路径。

### 6.1 抖音

```bash
sau douyin login --account <别名>
sau douyin check --account <别名>
sau douyin upload-video --account <别名> --file videos/demo.mp4 --title "标题" --desc "简介" --tags 标签1,标签2
sau douyin upload-note --account <别名> --images img/1.png img/2.png --title "图文标题" --note "正文" --tags 标签1,标签2
```

### 6.2 快手

```bash
sau kuaishou login --account <别名>
sau kuaishou check --account <别名>
sau kuaishou upload-video --account <别名> --file videos/demo.mp4 --title "标题" --desc "简介" --tags 标签1,标签2
sau kuaishou upload-note --account <别名> --images img/1.png img/2.png img/3.png --title "图文标题" --note "正文" --tags 标签1,标签2
```

### 6.3 小红书

```bash
sau xiaohongshu login --account <别名>
sau xiaohongshu check --account <别名>
sau xiaohongshu upload-video --account <别名> --file videos/demo.mp4 --title "标题" --desc "简介" --tags 标签1,标签2
sau xiaohongshu upload-note --account <别名> --images img/1.png img/2.png img/3.png --title "图文标题" --note "正文" --tags 标签1,标签2
```

### 6.4 Bilibili

```bash
sau bilibili login --account <别名>
sau bilibili check --account <别名>
sau bilibili upload-video --account <别名> --file videos/demo.mp4 --title "标题" --desc "简介" --tid 249 --tags 标签1,标签2
```

- `--tid`：分区 ID，需按你稿件实际分区修改（示例 `249` 仅为文档占位）。
- `biliup` 由程序在需要时自动下载/更新，一般无需手动安装。
- 登录建议在**本机真实终端**中执行，便于扫码。

**元数据约定（与文档一致）**：

- 视频：`title` + `desc` + `tags`
- 图文：`title` + `note` + `tags`

---

## 7. 常用参数

### 7.1 定时发布

不传 `--schedule` 则一般为**立即发布**。定时示例：

```bash
sau douyin upload-video --account <别名> --file videos/demo.mp4 --title "标题" --desc "简介" --schedule "2026-04-17 21:30"
```

各平台 `upload-video` / `upload-note` 及 B 站 `upload-video` 均支持（具体以 `sau <平台> <子命令> --help` 为准）。

### 7.2 视频附加参数（节选）

- 通用：`--thumbnail 封面图.png`（见 `docs/CLI.md`）

### 7.3 无头 / 有头 / 调试

- 默认偏**无头**（后台浏览器）。
- 需要看页面时加 **`--headed`**；强制无头可加 **`--headless`**。
- 排查问题时加 **`--debug`**（失败时保留更多调试信息）。

### 7.4 图文注意事项（摘要）

- 抖音图文：最多 35 张图，不支持 GIF。
- 快手图文：建议多张图使用不同文件路径，避免同一路径重复传多次。
- 小红书：`--note` 可选，建议始终显式传 `--title`。

---

## 8. 其他平台（`examples/`）

历史或直连 uploader 的入口示例，按需阅读脚本内注释与参数：

| 文件 | 说明 |
| --- | --- |
| `examples/upload_to_douyin.py` | 抖音 |
| `examples/upload_video_to_bilibili.py` | B 站 |
| `examples/upload_to_kuaishou.py` | 快手 |
| `examples/upload_video_to_xiaohongshu.py` | 小红书 |
| `examples/upload_video_to_tencent.py` | 视频号 |
| `examples/upload_video_to_baijiahao.py` | 百家号 |
| `examples/upload_video_to_tiktok.py` | TikTok |

主线维护重点在 **`sau` CLI**；Web 相关见 [docs/legacy-web.md](docs/legacy-web.md)，不保证与当前 CLI 完全同步。

---

## 9. 常见问题

| 现象 | 建议 |
| --- | --- |
| 找不到 `sau` | 确认已 `activate` 虚拟环境，并在项目根执行 `uv pip install -e .` |
| 浏览器/Chromium 报错 | 执行 `patchright install chromium`；国内可配 `PLAYWRIGHT_DOWNLOAD_HOST` 镜像 |
| B 站二维码异常 | 在本机终端登录；查看目录下 `qrcode.png` |
| B 站 biliup 下载慢 | 可参考 [docs/install.md](docs/install.md) 中的 GitHub 代理说明 |

---

## 10. 延伸阅读

- 安装与更新：[docs/install.md](docs/install.md)、[docs/update.md](docs/update.md)
- CLI 完整说明：[docs/CLI.md](docs/CLI.md)
- 给 AI Agent 的启动提示：[docs/agent-bootstrap.md](docs/agent-bootstrap.md)
- 各平台 Skill（给 OpenClaw / Codex 等）：`skills/*/SKILL.md`
- 官方文档站点：<https://sap-doc.nasdaddy.com/>
