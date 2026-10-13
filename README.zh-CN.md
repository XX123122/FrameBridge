# FrameBridge

为 Windows 与 Codex 提供本地 ChatGPT 网页图片生成流程：人工授权、单次提交、正常下载和文件验证。

[English](README.md) | 简体中文

FrameBridge 读取本地 Prompt 与明确指定的参考图，由当前用户选择浏览器会话并授权一个任务，再用 Playwright 操作正常页面、保存并校验结果。它是**非官方**的个人学习工具，不调用付费 OpenAI API，不提供公开 API，也不绕过账号限额。

## 演示

**目前没有已审核可公开的软件运行录屏。** 请看[录制指南](docs/DEMO_RECORDING.md)和[素材要求](docs/assets/README.md)。演示链路为：Prompt 文件 → 用户手动登录的可见浏览器 → 单任务授权 → 生成 → 正常下载 → 本地校验。模拟测试页面不能当作真实软件演示。

## 核心功能

- UTF-8 txt/md 与明确列出的 PNG/JPEG/WebP 参考图；保留原始字节与快照。
- 串行任务、四种主状态与独立的待确认标记；不自动遍历全部队列。
- 一条命令准备、一次发送、等待、正常下载、格式/像素/尺寸/哈希验证。
- 恢复只收集原请求结果，不重发；已有图片不覆盖。
- 进度与本地 JSON/Markdown 耗时报告。
- 可移植的 Codex Skill；安装不等于登录、配置 CDP 或授权生图。

## 已验证能力与限制

| 范围 | 证据与边界 |
| --- | --- |
| Windows、可见 Edge、中文 ChatGPT UI、纯 Prompt 生图/下载 | 曾有 3 次维护者明确授权的单图实测；见[历史实验](docs/HISTORICAL_EXPERIMENTS.md) |
| Python 3.11、Playwright、Pillow | 维护者本地历史测试；新版本本地结果见[发布就绪记录](docs/RELEASE_READINESS.md) |
| 状态、恢复、格式、上传、UI 边界 | 离线逻辑和浏览器模拟，不证明真实参考图上传已验证 |
| 有限串行实测 | 两张校验保存、一项被拒绝；失败即停，人工确认后继续，见[排队记录](docs/QUEUE_TRIAL.md) |
| Chrome、其它 UI 语言/版本 | CDP 适配器可接入，不声称有相同真实兼容性证据 |
| 真实参考图上传、人物身份一致性 | 未做真实验证；上传控件只做过模拟测试 |
| 大队列 | 未做真实验证；仅观察过上述有限串行流程 |
| GitHub CI、v0.1.0 | 只完成准备；远程运行与发布需另行核对 |

生成耗时、质量、额度和 UI 变化都不保证。当前图片模式准备使用中文控件标签。K01/K02/K03 是特定环境的历史证据，不代表新用户已配置或已授权，也不代表固定性能。CI 未实际成功前不显示 passing 徽章。

## Quick Start

需要 Git、Python 3.11+、Windows PowerShell 与自行安装的 Edge。历史实测解释器为 Python 3.11；新增 CI 版本在远程运行前均待验证。当前是 v0.1.0 发布准备，没有声称已打 Tag/发布。

```powershell
git clone https://github.com/XX123122/FrameBridge.git
cd FrameBridge
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-browser.txt
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py init
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py doctor
```

这些命令针对拟发布源码；未合并的本地变更可能尚未出现在远程默认分支。初始化/doctor 不消耗图片额度，也不证明浏览器可用。安装依赖使用当前用户的包索引，先检查其配置。

### 配置自己的浏览器

新用户默认未登录、未配置、未授权。先阅读[接入指南](docs/SETUP.md)，只查看启动计划：

```powershell
.\scripts\start_edge.ps1 -DryRun
```

只有决定启用独立可见会话与仅本机调试后才执行：

```powershell
.\scripts\start_edge.ps1 -ConfirmLocalControl
```

浏览器自行管理项目目录之外的独立 profile。找不到安装时用 `-EdgePath`，需要时用 `-Port`。用户自行登录并核对账号，检查监听只在 `127.0.0.1`/`::1`，不开放或转发公网，不复制默认 profile，不改组织策略。

对你明确配置的端口做零额度检查：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 --page https://chatgpt.com/ probe
```

### 准备、确认、生成

```powershell
Copy-Item prompts/example.md prompts/my-image.md
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py add EXAMPLE --prompt prompts/my-image.md --output outputs/EXAMPLE.png
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py packet EXAMPLE
```

在 add 前编辑副本；快照保留原文。参考图逐个用 `--reference references/file.png` 指定。不消耗图片额度。下一次用新 ID、新输出路径。

**当前用户明确批准这个 Prompt、参考图和下载后：**

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 generate EXAMPLE --confirmed --timeout 300
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check EXAMPLE
```

`--confirmed` 记录用户同意，不是平台授权。输出在 outputs/，快照和日志在 logs/，状态在 tasks.json；这些运行文件不随源码公开。验证、额度、权限或结果不明确时停止，按[恢复指南](docs/USAGE.md)收集原结果，不再次提交。

## Codex Skill

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/install_skill.py
```

默认入口位于 `$CODEX_HOME/skills/framebridge-web-imagegen` 或 `~/.codex/skills/`。安装只写入口和项目路径，不启动浏览器、登录、装扩展或授权生图；按自己的 Codex 版本重新加载技能发现。参考[官方 Skill 文档](https://learn.chatgpt.com/docs/build-skills)。

示例：“使用 $framebridge-web-imagegen，准备 prompts/my-image.md 和我明确列出的参考图。先展示任务；我确认前不要生图。”

项目移动或更新后，从新目录明确更新：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/install_skill.py --update
```

也可用 `--project` 指定新位置。旧版无安装元数据的入口需单独检查，再选择 `--update --adopt-existing`；其它 Skill 不覆盖，见[迁移说明](docs/SETUP.md)。

## 工作原理

通过本地任务账本与标准 Playwright，实现 ChatGPT image generation with Codex。只连接用户明确选择的 loopback CDP，匹配原对话唯一新结果，再通过正常 Download 事件完成 Playwright ChatGPT image download；没有私有模型调用或认证导出。

```text
本地 Prompt/明确参考图 → 原始快照 → 当前用户授权
→ 可见网页：一次 Send → 观察完成 → 正常 Download
→ 文件验证 → 本地状态与耗时报告
```

耗时从 Send 到页面完成与保存计算，含轮询/复核延迟，不是服务端纯计算时间。浏览器运行和离线模拟分开。

## 安全与服务条款

网页自动化**不是官方 API**。OpenAI [个人服务条款](https://openai.com/policies/terms-of-use/)禁止自动/程序化提取输出；正常按钮、订阅、低频或个人用途不构成许可。用户同意不能替代平台授权，请自行核对适用条款。

不使用付费 API、stealth、验证码破解、认证导出、私有模型接口或限额绕过。CDP 仅本机。Issue 不附 Cookie、Token、密码、私人对话 URL 或原始日志。[安全策略](SECURITY.md)、[风险说明](docs/RISKS.md)、[审查记录](docs/PROJECT_AUDIT.md)提供具体边界。诊断截图/对话文本需明确选择，仍可能包含个人信息。

## FAQ

**用哪个账号生成？** 使用指定浏览器里的 ChatGPT 账号，可与 Codex 不同，不迁移凭证。

**失败能恢复吗？** 先核对原会话与状态，再明确使用 collect 收集；不会重发。本地中断不等于取消远端请求。

**英文文档代表英文 UI 已验证吗？** 不代表，已实测的准备控件是中文；不能定位就停止。

**参考图和人物身份已验证吗？** 路径/格式/上传控件有离线测试，真实上传和一致性未验证；模型可能不遵守全部约束。

**能无人值守公开服务吗？** 不在范围内，授权、限制、UI 和条款风险仍存在。

## Contributing / License

按 [CONTRIBUTING.md](CONTRIBUTING.md) 做离线检查和小范围修改，用模板提交脱敏 Issue；敏感报告看 [SECURITY.md](SECURITY.md)。[发布就绪记录](docs/RELEASE_READINESS.md)区分本地检查、CI 与发布， [v0.1.0 说明](docs/RELEASE_NOTES_v0.1.0.md)仍是草稿。

MIT — [LICENSE](LICENSE)。不声称得到 OpenAI/Microsoft 背书。
