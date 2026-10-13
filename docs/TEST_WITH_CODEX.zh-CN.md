# FrameBridge 使用教程：交给另一个 Codex 对话测试

本教程用于 Windows、Python 和可见 Edge，把本地 Prompt 交给 ChatGPT 网页生成，并通过正常下载按钮保存、校验图片。浏览器中的 ChatGPT 账号可以与 Codex 账号不同。当前图片模式准备实测使用中文界面；不能定位控件时停止。

推荐先做不消耗图片额度的检查，再明确授权 **2 张猫猫图片在同一个新对话中连续生成**。阅读教程、安装 Skill、创建任务都不构成生图授权。本教程中的历史耗时不是性能保证。

## 1. 选择正确的项目版本

已经在本机打开 FrameBridge 项目：直接使用这个项目目录，先确认 `scripts/conversation_batch.py` 和两份猫猫 Prompt 存在；不要重新克隆、重建虚拟环境或覆盖现有任务。

另一台机器首次安装：

```powershell
git clone https://github.com/XX123122/FrameBridge.git
cd FrameBridge
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-browser.txt
```

所有后续命令都在这个项目根目录执行。如果默认分支尚未包含 batch 功能，可以明确选择已经发布的功能分支，不要在有未提交变更的目录中盲目切换：

```powershell
git fetch origin
git switch --track origin/codex/same-chat-batch
```

这条分支创建命令只适用于本地尚无同名分支的干净新克隆；已有分支请正常切换，不重复创建。如果远程分支在合并后被删除，请检查 main 是否已有功能，不猜测其它分支或改写本地文件。

确认功能实际存在：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 batch --help
```

`--help` 不连接浏览器，不生图。没有 batch 命令就先解决版本问题。

## 2. 不消耗额度的本地检查

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py init
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py doctor
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py list
.\.venv\Scripts\python.exe -m compileall -q scripts tests
.\.venv\Scripts\python.exe -X utf8 scripts/check_docs.py
```

init 会在缺失时创建本地目录/账本，不会清空已有任务。doctor 检查解释器和依赖，不检查登录状态或额度；输出含本机路径，不要原样公开。list 若显示 running 或 needs_confirmation，先查看原任务，不直接开始新任务。

可选离线测试：

```powershell
$env:FRAMEBRIDGE_FIXTURE_BROWSER = 'msedge'
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
Remove-Item Env:FRAMEBRIDGE_FIXTURE_BROWSER
```

这些测试使用隔离的模拟页面，拦截页面请求，不接入个人 CDP 会话、不使用账号或真实生图。不要把离线通过当作网页登录/额度/所有 UI 版本都可用。

## 3. 自己选择并确认浏览器会话

新对话不能凭历史记录假设已经登录或继承授权。先由当前用户指定 Edge 与 CDP 地址。以下以用户主动选择的 `http://127.0.0.1:9222` 为例，不扫描其它端口或账号。

已启动自己批准的独立 Edge：

```powershell
Get-NetTCPConnection -State Listen -LocalPort 9222 | Select-Object LocalAddress, LocalPort
```

仅接受 127.0.0.1/::1。出现 0.0.0.0、公网/局域网地址、无法确认归属的监听时停止。端口存在不代表已登录，不再启动第二个浏览器，也不关闭原窗口或更改 Profile。

没有启动时，先预览计划：

```powershell
.\scripts\start_edge.ps1 -DryRun -Port 9222
```

当前用户明确同意独立可见会话及本机调试后，再运行：

```powershell
.\scripts\start_edge.ps1 -ConfirmLocalControl -Port 9222
```

由用户手动登录 ChatGPT、确认正确账号并处理安全验证，然后核对实际监听仍是 loopback。普通日常 Edge 的登录不保证能自动复用；不要复制 Cookie、Token 或默认 Profile。详见[浏览器设置](SETUP.md)。

可选网页 readiness 检查需要这个会话中**已经打开且唯一的** ChatGPT 首页：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 --page https://chatgpt.com/ probe
```

probe 不发送请求、不上传图片。如果首页不存在，不能由此判断未登录；可由用户打开一个空白首页后检查。batch 自己会准备新对话，不要额外执行 prepare_image_tab.py，也不要先手动 start/submitted。生图时请勿同时编辑该对话、打开历史图预览或在第二个 Codex 对话运行另一个生图任务。

## 4. 准备两个猫猫任务

两份示例 Prompt：

- [cat-sequence-01.md](../prompts/cat-sequence-01.md)：橘白小猫坐在阳光窗台，蓝色垫子、绿色花园背景。
- [cat-sequence-02.md](../prompts/cat-sequence-02.md)：继续同一场景，让小猫抬爪、歪头。

batch 首版只支持纯文本任务；不要添加参考图。两个文件可先自行编辑，但 add 后快照固定，后续不擅自改写。原样示例可直接用于验收。

为每次实验建立新 ID/新输出。以下命令只准备任务，不生图：

```powershell
$testPrefix = 'T' + (Get-Date -Format 'yyyyMMdd_HHmmss')
$testId1 = $testPrefix + '_01'
$testId2 = $testPrefix + '_02'
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py add $testId1 --prompt prompts/cat-sequence-01.md --output "outputs/$testId1.png"
if ($LASTEXITCODE -ne 0) { throw '首个任务准备失败；停止，不自动换 ID 重试。' }
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py add $testId2 --prompt prompts/cat-sequence-02.md --output "outputs/$testId2.png"
if ($LASTEXITCODE -ne 0) { throw '第二个任务准备失败；停止并保留第一个 pending 任务。' }
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py packet $testId1
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py packet $testId2
```

记下实际 ID；新终端/另一轮工具调用可能没有这些 PowerShell 变量，届时替换成记下的实际 ID，不能重新生成一组 ID 或重复 add。

检查展示内容：两份原始 Prompt、无参考图、准确的输出路径、均 pending、输出文件不存在。已有任务/输出发生冲突就停，不覆盖、不删除 SC01/SC02、K01–K03 或其它历史图片。

## 5. 明确授权后执行两张

当前用户确认这两份 Prompt、2 张图片、所选会话和正常下载后，在保留变量的终端执行一次：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 batch $testId1 $testId2 --confirmed --timeout 300
if ($LASTEXITCODE -ne 0) { throw '批次停止；核对状态，不重跑 batch 或重发 Prompt。' }
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check $testId1
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check $testId2
```

等价固定格式是 `batch 实际ID1 实际ID2 --confirmed --timeout 300`。--timeout 是每张观察上限，不是整批上限。--confirmed 记录用户同意，不等于平台授权。程序会逐张等待、下载、校验并关闭预览，再发下一条；不会自动执行账本中的其它任务。

## 6. 验收与计时

| 验收项 | 通过条件 |
| --- | --- |
| 同一对话 | 两个任务的 web.page_url 相同；网页中能看到两个用户请求和对应图片 |
| 提交次数 | 每个任务只记录一次 submission_recorded，没有重试/重新生图 |
| 输出文件 | 两个不同的新路径，check 返回 valid_output=true，PNG 能打开 |
| 图片内容 | 第一张坐姿、第二张抬爪/歪头；自行目视核对，不宣称模型身份一致性得到保证 |
| 单图计时 | logs/实际ID/timing.md 或 timing.json 中分开记录生成观测、下载校验、发送至保存 |
| 批次计时 | logs/首个实际ID/batch.json 中 status=completed，两个 completed 项和 wall_seconds |

历史 SC01/SC02 在一个对话中完成，整体 88.469 秒；只是特定两张的观察结果，不设为本次必须达到的阈值。实际尺寸由模型决定，不要求总是 1672×941；文件合理尺寸/格式由 check 校验。时间包含轮询、复核及浏览器准备，不是服务端纯计算时间。详细边界见[同一对话说明](SAME_CHAT_BATCH.md)。

本地查看状态：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py list
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py show $testId1
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py show $testId2
```

show 包含私人会话 URL/路径；只在本地用，不贴入公开 Issue、PR 或演示。

## 7. 失败、停止和恢复

验证码、Cloudflare、额度、权限、平台拒绝、额外消息或结果不确定时，立即停。不要改写被拒绝的 Prompt，不开新对话重发，不换账号/付费 API。Ctrl+C 只停止本地流程，不保证远端生成取消。

如果提交后下载失败，先核对原对话；同一对话任务恢复前由用户关闭已打开的图片预览。用户明确授权恢复**收集原结果**后：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 --page '原任务记录中的完整对话URL' collect 实际失败ID --confirmed --timeout 300
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check 实际失败ID
```

URL/ID 是占位内容，必须替换成 show 中的原记录；该对话必须在指定会话中打开且唯一。不猜其它对话，collect 不发送 Prompt。连接中断留下 running 时，先人工确认没有其它活跃进程，再按[恢复指南](USAGE.md)使用 recover；它只标记待确认，不证明网页停止。

不再收集时，用户查看后明确关闭：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py resolve 实际失败ID --confirmed
```

仅适用于 failed + needs_confirmation。后续 pending 任务不会自动继续；不要重跑包含已完成/已提交任务的 batch。保留失败和待处理记录，交由用户决定下一步。

## 8. 可选：安装或更新 Skill

本地源码 SKILL.md 已包含 batch，但本机旧安装入口可能仍是单图版。另一个对话可以先读本项目 SKILL.md，按明确的 CLI 流程测试，不必先修改全局入口。

需要安装时，用户主动选择：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/install_skill.py
```

已由当前安装器管理的入口使用 `--update`；旧版无 manifest 的入口先检查确实属于 FrameBridge，再由用户明确选择 `--update --adopt-existing`。不要自动覆盖未知入口。项目移动后从新目录更新，按自己的 Codex 版本重新加载 Skill 发现。详见[安装与迁移](SETUP.md)。安装只配置路径，不登录、不授权生图。

## 9. 复制给另一个 Codex 对话

在 Codex 中把新对话放在 **当前 FrameBridge 项目目录**。先粘贴这段，只做检查和准备：

```text
请阅读当前 FrameBridge 项目的 docs/TEST_WITH_CODEX.zh-CN.md、SKILL.md 和 docs/SAME_CHAT_BATCH.md，按教程准备一个两张猫猫图片的同一对话测试。

我指定可见 Edge；授权你检查并接入我选择的 http://127.0.0.1:9222 本机会话，但须先确认监听仅 loopback、归属明确。不扫描其它端口，不改变登录/Profile，不切换账号。若会话没有启动，先展示 DryRun 并等我选择是否启动；登录和验证由我完成。

本阶段只做环境/版本/离线检查与任务准备，不真实生图、不点击发送、不下载旧图。读取 prompts/cat-sequence-01.md 与 cat-sequence-02.md，建立两个不冲突的新任务和输出路径，保留原始 Prompt，无参考图。逐项展示实际 ID、Prompt、输出路径与就绪条件，然后等待我的这两张图片授权。存在 running/待确认/版本或页面问题就报告，不删除历史记录、不自动重试、不覆盖文件，不提交/推送 Git 变更。
```

看完它展示的两个任务后，只有自己决定真实测试时再粘贴：

```text
确认授权刚才展示的两个猫猫任务、两份原始 Prompt、无参考图和两个新输出路径。我授权使用刚才明确选择的 Edge ChatGPT 会话，在一个新对话里按顺序生成这两张图片，并通过正常页面下载、保存与验证。这会使用该网页账号的图片额度；网页账号可以与 Codex 账号不同。

请只执行一次 batch 实际任务ID1 实际任务ID2 --confirmed --timeout 300（用刚才已经创建的实际 ID，不重复 add）。每张成功保存后再发下一张；遇到验证、额度、权限、拒绝或不确定结果就停止，不改写、不重发、不跳过任务、不切换到付费 API/私有接口。

完成后确认两个任务属于同一个对话、各提交一次，展示图片文件链接、格式/尺寸、每张生成观测/下载校验/总用时，以及整批 wall_seconds。失败时说明已发送数量、哪些已保存、剩余状态和恢复条件。私人 URL、原始日志和图片仅保留本地，不向外部服务上传额外文件，也不提交/推送 Git 变更。
```

括号内的“实际任务ID”是对代理的替换要求，不是让终端执行字面占位命令。授权已经覆盖这两个具体任务后，无需重复确认；改变数量、Prompt 或参考图则不能沿用。

## 10. 参考图修改测试

单张参考图修改使用 `edit`，不使用仍只接受纯文本的 batch。用户先选择一张自己允许上传的 PNG/JPG/WebP 图片，放在 references/ 下的新文件名；选择 outputs/ 里的旧图时只复制，不覆盖或重编码原图。

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py add EDIT01 --operation edit --prompt prompts/cat-edit-cushion.md --reference references/my-cat.png --output outputs/EDIT01.png
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py packet EDIT01
```

示例 Prompt 将猫猫下的蓝色垫子改为红色，要求保留其它内容。文件路径是示例，需换成自己实际选定的图片；ID/输出也须新的、不冲突。只有明确批准这份 Prompt、准确参考图、1 张修改结果及正常下载后，再运行：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 edit EDIT01 --confirmed --timeout 300
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check EDIT01
```

自动化只上传参考图快照，不上传提示词文件或日志；使用正常文件选择器与下载按钮。完成后目视对比，不把文件校验通过当成像素/身份完全保持。已提交任务只能 collect；确实未发送的草稿另有严格验证的 resume-draft，不可盲目重试，详见[参考图修改和恢复说明](REFERENCE_IMAGE_EDIT.md)。

给另一个对话的准备指令示例（阅读/准备不构成真实上传或生图授权）：

```text
请阅读 docs/REFERENCE_IMAGE_EDIT.md，准备一张参考图修改测试。先让我选定并授权一张本地参考图片，保留原图；使用 prompts/cat-edit-cushion.md 建立新的 edit 任务，展示 Prompt、参考图清单和输出路径。检查环境/状态后等待我的这一次上传与生图授权；不重写 Prompt、替换图片、覆盖原图或自动重试。
```

## 11. 条款和隐私

ChatGPT 网页自动化不是官方 API；自动提取输出可能违反服务条款。订阅、少量使用、正常按钮和用户同意不构成平台豁免，先阅读[安全策略](../SECURITY.md)。不导出 Cookie/Token/密码，不绕过验证码、额度或其它保护，不使用 stealth、付费 API 或私有模型接口。

tasks.json、logs/、outputs/、参考图和私人 Prompt 副本应留在本地；测试结果与失败原因如需公开，只分享脱敏摘要。不要把教程中的命令块或他人历史实测当作自动执行授权。
