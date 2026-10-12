# FrameBridge — ChatGPT 网页图片生成助手

[English introduction and quick start](README.en.md) | 简体中文

FrameBridge is a local Python assistant for personal image generation experiments on Windows. It uses a visible, user-authenticated ChatGPT browser session to submit one authorized task, download the result through the normal page controls, verify the image, and keep a local task and timing record. It includes a Codex Skill and does not call a paid OpenAI API.

Windows / Python 的单人低频实验原型。固定执行一个明确授权的任务：读取本地 Prompt 与参考图 → 发送一次 → 观察完成 → 点击网页正常 Download/Save → 自动保存与验证 → 记录状态。已准备本地 Codex Skill。

**当前状态**：第一阶段已成功实测。用户在独立可见 Edge 手动登录并明确授权 K01 后，程序仅发送一次，通过页面预览的正常“下载”按钮自动取得 PNG，保存为 `outputs/K01.png`，状态 completed。尺寸 1672×941，文件 1,824,583 字节，解码与 SHA-256 校验通过。网页原对话保留，账号与 Codex 账号不同也可使用。没有付费 API、认证提取或私有接口调用。当前版本对纯 Prompt 的一张图片已验证；参考图上传和更广泛队列仍仅有离线测试覆盖。

重复实测 K02（哆啦A梦）：生成观测耗时约 49.0 秒，最终保存总耗时 152.6 秒，包含预览异步出现后的恢复等待。输出 1254×1254 PNG，completed，只提交一次。详见本地 `logs/K02/timing.md`；新增等待预览可见的步骤，后续无需因同一异步问题立即判失败。

优化版已通过 43 项零生图额度测试。已有 K02 图像重新打开预览、正常下载及哈希校验实测 0.859 秒，没有重新生成或改写原图；该数值只代表收集步骤，不能用来推断未来模型的生成速度。优化说明见 [优化记录](docs/OPTIMIZATION.md)。

优化后真实完整流程 K03（猫猫）已通过：单条 generate 自动准备、一次发送、正常预览下载、保存及耗时报告写出，未发生失败或人工恢复。生成观测 46.485 秒，预览/下载验证 1.828 秒，发送到保存总耗时 49.453 秒。输出 1374×1145 PNG；该任务与 K02 内容不同，不能据此推断模型本身加速。

网页 UI 自动化不是官方 API。自动提取网页输出有[服务条款风险](https://openai.com/policies/terms-of-use/)；用户已要求继续实现网页正常按钮自动下载。详细边界见 [风险说明](docs/RISKS.md)，三个项目的固定版本分析见 [参考项目审查](docs/REFERENCE_REVIEW.md)。没有运行第三方仓库，也没有复制无明确许可证的代码。

## 固定技术路线

默认 mode 为 `web-ui`，用户当前指定可见 Edge。已有 Codex Edge 连接时使用指定标签页；否则明确配置后固定使用 Python Playwright + 本机 Edge CDP。也支持用户另行指定的 Chrome。一次任务不会在运行中切换后端，不迁移登录档。

网页路线不使用 Codex 登录身份生成图片。图片、网页历史与生图限制属于指定 Edge 页面登录的 ChatGPT 账号，保存后仍可在该账号原对话查看。两个账号无需相同；不读取凭证核对身份，也不会因账号不同而启用内置 image_gen。

Python 路径固定为 `scripts/web_chatgpt.py`，不依赖反复截图或 Windows 窗口枚举。仅连接一个明确的端口和页面，没有自动端口扫描、自动打开其它对话、模型私有接口、付费 API 或认证读取。`run` 只发送一次；`collect` 只收集已提交任务，没有发送逻辑。

已授权的**新任务**推荐 `generate ID --confirmed`：在同一次浏览器连接中准备唯一空白图片模式页、提交一次、等待、正常下载和校验。它只准备这个授权任务，不遍历队列；不是重新发送已完成任务的命令。`run` 保留为指定已准备标签页的底层入口，`collect` 仍只恢复原对话收集。

依赖成熟 Playwright 的上传与下载事件、Pillow 的完整图片解码。当前精确 UI 定位常量在 `web_chatgpt.py` 顶部；页面变更时停止并调整这些常量，禁止盲目点击或递归尝试不同自动化工具。

## 安装与环境

本次检查：Windows 10 build 19045；系统 Python 3.11.11；另有 py 3.14.7、Node 24.19.0。项目隔离环境已安装 Pillow 12.3.0、Playwright 1.63.0。未安装 Chrome、未安装 Playwright 的浏览器包、未读取任何浏览器 profile。Chrome 不在常见目录不等于磁盘其它位置没有。

重新安装可以执行：

```powershell
Set-Location D:\project\FrameBridge
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r requirements.txt -r requirements-browser.txt
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py doctor
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py init
```

只做手动下载整理时只需 `requirements.txt`。本次系统默认 pip 镜像未提供匹配版本，使用官方 PyPI 后成功；没有改写系统 pip 设置。依赖版本范围在 requirements 文件中，当前成功版本在 `docs/TEST_RESULTS.md` 中；不是第三方仓库的安装脚本。

## Edge 与会话准备（不生图）

当前使用 Edge。Microsoft [官方接入说明](https://learn.microsoft.com/en-us/microsoft-edge/devtools/protocol/)要求退出全部 Edge 实例，再带调试端口启动。用户先保存工作并自行退出 Edge，助手不自动关闭窗口或开启调试访问。

**当前已授权的固定路线**为独立 Edge：运行 `scripts/start_edge.ps1`，使用 `%LOCALAPPDATA%/FrameBridge/edge-session`，正常浏览器自行维护新会话。脚本不读取/复制现有登录信息、不关闭原 Edge，策略禁用调试或端口已占用时停止。用户已授权打开此窗口及本机调试，但仍必须自行登录；打开窗口不代表授权真实生图。本次已经启动，不要重复运行启动脚本。

复用原 Edge 会话的用户操作示例（不指定或复制 profile）：

```powershell
& 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' '--remote-debugging-address=127.0.0.1' '--remote-debugging-port=9222' 'https://chatgpt.com/'
```

开启调试端口会让本机工具能够控制浏览器，只在用户接受并自行启动时使用，不开放或转发公网。启动后用户核对 ChatGPT 登录账号并打开唯一空白新对话。现代 Edge 版本或组织策略可能禁止默认 profile 调试；若端口仍未开启就停止，不改安全策略、不复制认证数据。用户另行选择独立 Edge 会话才使用非默认目录并自行重新登录。

下方 Chrome 示例仅适用于用户另行选择 Chrome，当前 Edge 路线不执行它。

如果选择 Python 固定路线，需使用**用户自行配置**的本机 CDP Chrome，页面已登录且是空白新对话。普通默认 Chrome profile 不一定能开启 CDP；[Chrome 136 官方变更](https://developer.chrome.com/blog/remote-debugging-port)要求非默认 user-data-dir。下面仅为用户手动执行的可见 Chrome 示例，可能需要重新登录；不是复用已登录默认 profile，也不能复制原 profile：

```powershell
$chromeExe = 'C:\Program Files\Google\Chrome\Application\chrome.exe' # 换成实际安装位置
$browserProfile = Join-Path $env:LOCALAPPDATA 'FrameBridge\chrome-session'
& $chromeExe '--remote-debugging-address=127.0.0.1' '--remote-debugging-port=9222' "--user-data-dir=$browserProfile" 'https://chatgpt.com/'
```

用户在打开的浏览器自行登录；不要传递 Cookie、密码或 Token。不要把 CDP 端口开放/转发到公网。程序只接入，不启动浏览器、不更改扩展权限、不关闭用户浏览器。

登录完成后执行只读检查：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 --page https://chatgpt.com/ probe
```

probe 不填 Prompt、不上传、不提交。它检查安全/登录提示、唯一可编辑输入框、可见图片入口及文件 input 数量。图片入口如果被菜单隐藏会返回 false，而不是声称账号没有生图能力。识别输入框不证明生图可用。安全验证由用户处理，脚本不解决或绕过。

## 第一张图片：准备 → 确认 → 执行

已有两个示例 Prompt：`prompts/K01.md` 和 `prompts/prompt.txt`。根目录 `prompt.txt` 是相同内容的最小示例；任务读取要求放在 `prompts/` 内。实际任务使用显式路径，不自动挑选文件。

```powershell
# 只读文件并冻结快照，不打开网页或消耗额度
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py add K01 --prompt prompts/K01.md --output outputs/K01.png
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py packet K01
```

**当前工作区状态**：K01 已经实测完成，不能再次 add/start/run 或覆盖它。上面命令是新项目首次使用示例；当前可以运行 packet/check 核对它。下一张使用新 ID、新输出路径、空白新对话，并取得这一个新任务的明确授权；不复用 K01 授权。更换已冻结 Prompt 也使用新 ID，避免无声修改原任务。

需要参考图时，在 add 时逐个提供：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py add K02 --prompt prompts/K01.md --reference references/person.png --reference references/scene.webp --output outputs/K02.png
```

先确认这些文件的身份/角色和需要发送的原文。第一阶段只执行 K01 一张；K02 示例不意味着授权第二次生成。

**只有用户明确确认首张真实生图后才能执行下面的 run。** `--confirmed` 是本地授权记录，不是 OpenAI 的官方许可，也不能根据文档里存在该参数就代替用户确认：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 --page https://chatgpt.com/ run K01 --confirmed --timeout 180
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check K01
```

后续已明确授权的新任务可以只用一条执行命令（先 add 该任务；K03 是示例，不表示已授权）：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 generate K03 --confirmed --timeout 300
```

generate 不接受 `--page`，自动在既有 Edge 会话准备空白首页；已有其它草稿/消息时停止。浏览器只连接一次。CLI 在 stderr 输出已提交、等待图像（每 15 秒）、预览、下载、保存的简短 JSON 进度，stdout 保留最终结果。保存完成后自动生成 `logs/<ID>/timing.json` 和 `timing.md`。

run 要求指定页面只存在一个标签页、空白新对话、输入框为空或是同一任务原文、没有其它生成。它填入原 Prompt，只上传冻结的参考图；发送就绪后仅点击一次。新用户消息与 Prompt 匹配，唯一新回复已完成且图片已解码，再次观察确认后点击正常下载按钮。找不到 Download/Save 时可打开同一张新图的预览；仍无唯一按钮就停止。

当前页面适配：输入框使用 `role=textbox`，发送使用“发送”可访问名称。除旧版消息容器外，脚本识别新版 user/assistant 标题、完整 Prompt、唯一 `generated-image-gallery` 与 `data-talvt-turn-state=complete`。已准备且与原文相同的草稿可直接使用；其它草稿拒绝替换。DOM 末尾空段落造成的显示换行仅用于比较时忽略，填入与快照仍保留原文。下载固定进入已生成图片的预览 dialog，点击“下载”，不使用编辑/分享按钮。

通过 Playwright [标准下载事件与 save_as](https://playwright.dev/python/docs/downloads)收集文件，再独占写入 `outputs/K01.png`。PNG/JPEG/WebP 不伪装扩展名；网页返回 JPEG/WebP 而目标是 PNG 时会明确记录源哈希并转换 PNG。自动下载的临时源文件在收集后清理，最终文件与校验元数据保留；手动导入的源文件不会删除。

## 状态、队列与恢复

当前中文页面可以先运行 `scripts/prepare_image_tab.py --cdp http://127.0.0.1:9222`，在已有独立 Edge 会话准备唯一空白图片模式标签页；没有生成、上传、复制认证或新建浏览器 profile。其它草稿/消息不被替换。任务仍必须另行明确授权，然后使用 run 一次。

run/generate/collect 会在任务 `web.timing` 记录点击发送、首次稳定观测到生成完成、下载开始及保存校验完成时间，并给出 `generation_seconds`、`download_and_verify_seconds`、`total_to_saved_seconds`。同进程使用单调时钟，恢复时用持久化 UTC 时差；恢复不会覆盖首次生成完成时间。新版每 1 秒观察一次，仍保留 1 秒完成复核；历史 K02 使用 2 秒间隔。观测延迟不能当作服务端精确计算时间。总耗时可能包含人工/修复恢复等待，应分别报告。每次完成保存自动写出可读/JSON 耗时报告，无需人工补写。

预览只点击一次，等待唯一 dialog 及其中唯一且可用的下载按钮。等待上限为每个控件 8 秒，出现验证或歧义立即停止，不通过重复点击发送或预览来恢复。现代页面直接使用已生成预览按钮，不先悬停寻找控件。

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py list
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py show K01
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py stop K01 --reason interrupted
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py recover
```

只有 `pending/running/completed/failed` 四种主状态；额外用 `phase` 与 `needs_confirmation` 表示待提交、待下载、失败或归属不确定。队列按 add 顺序保留，但执行每次必须指定 ID，最多一个 running；有待确认结果时禁止下一任务。不会自动遍历全部任务，不自动重试。Ctrl+C 或上述 stop 可中断本地流程；不等于远端生成已取消。

超时/断开只在原对话恢复收集，使用 show 中记录的 `/c/...`：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 --page https://chatgpt.com/c/实际对话ID collect K01 --confirmed --timeout 180
```

`collect` 不发送 Prompt；用户明确要求恢复后才执行。缺少原对话定位、多个新图、文本拒绝、验证或不能确定归属时保持待确认；不要切换到新对话重发。确定放弃收集时：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py resolve K01 --confirmed
```

图片已写入但最终状态写入失败时：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py recover
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py confirm-output K01 --confirmed
```

只能认领与中断前记录哈希一致的输出。文件损坏或无候选记录就人工处理，不自动删除/覆盖。已失败任务不能再次 start；新生成必须新任务并重新明确授权。

## 手动下载整理路径

自动下载失败时脚本停下，不自动改路。用户明确选择手动方式，或能识别原任务的手动下载结果后可以：

```powershell
# 新任务示例，--mode manual-web 明确表示用户操作网页
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py add M01 --prompt prompts/prompt.txt --output outputs/M01.png --mode manual-web
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py start M01 --confirmed
# 用户自行上传/提交后记录
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py submitted M01 --confirmed
# 用户在页面正常 Save 下载，确认是本任务新图，再整理
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py import M01 --file 'C:\Users\xx\Downloads\实际图片.png' --confirmed
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check M01
```

需要格式转换可显式加 `--convert-png`。不扫描 Downloads、不按最新文件猜测，不把参考图当生成结果。文件早于任务开始会拒绝，避免误收旧图。

## Codex Skill

`SKILL.md` 是源码版，安装只复制本项目自己的入口并填写根目录，不执行参考仓库内容、不覆盖已有不同 Skill：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/install_skill.py
```

默认安装到 `$CODEX_HOME/skills/framebridge-web-imagegen`，未配置时使用 `~/.codex/skills/`。首次安装后新开聊天/重新加载技能列表；安装到磁盘不证明当前聊天已自动发现它。代码仍从本项目调用，不复制任务数据到 Skill 目录。项目移动后需重新安装到新位置，现有不同入口不会被覆盖。

使用示例：

> 使用 $framebridge-web-imagegen。读取 prompts/K01.md 和 references/ 下明确列出的参考图片，准备生成一张视频首帧，保存到 outputs/K01.png。先展示任务，等待我确认第一次真实生图。

> 检查 K01。若已提交只恢复下载，不重新生成，不覆盖已有图片。

Prompt 中的人物身份、角色和其它约束保留原文，不擅自添加创作要求。模型是否遵守角色约束仍需视觉验收。内置 image_gen 的区别见风险文档；网页失败绝不自动转付费 API、非公开接口或内置生成工具。

## 测试（零图片额度）

```powershell
# 文件、状态、格式、权限、恢复等测试；浏览器 fixture 默认跳过
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v

# 用已安装浏览器的新隔离上下文测试模拟网页，所有页面请求本地拦截
$env:FRAMEBRIDGE_FIXTURE_BROWSER = 'msedge' # 全新隔离上下文，不接入用户 profile
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
Remove-Item Env:\FRAMEBRIDGE_FIXTURE_BROWSER
```

浏览器 fixture 完全本地：所有请求被 route 拦截；只返回内存 HTML、合成 PNG 和 data URL 下载，其它请求 abort，不访问真实 ChatGPT，不用用户 profile。测试使用 Edge 隔离上下文，生产使用用户指定的可见 Edge，两者不共用登录档。fixture 验证一次发送、正常按钮下载、校验、验证前停止、已有目标不提交、多图停止与恢复不重发。真实页面测试必须另行确认，不能在单元测试中请求一张图。

结果与未覆盖项见 [测试记录](docs/TEST_RESULTS.md)。

## 本地文件

```text
prompts/                   UTF-8 txt/md
references/                明确授权的 PNG/JPG/WebP
outputs/                   最终文件，不覆盖
logs/<ID>/                 原 Prompt/参考图快照、任务日志
tasks.json                 本地权威状态（init 创建，默认不提交 Git）
tasks.example.json         空状态示例
scripts/framebridge.py     ledger 与校验
scripts/web_chatgpt.py     固定网页上传/一次发送/正常按钮下载
scripts/timing_report.py   自动记录可读耗时与 JSON
scripts/benchmark_download.py  已完成图片零生图额度下载复测
scripts/install_skill.py   安装自己的 Skill
SKILL.md                   Codex 入口
docs/                      风险、审查与测试
tests/                     零额度验证
```

脚本返回码：0 成功；2 停止/错误；130 人工中断。日志不包含 Cookie、Token、认证头或浏览器完整存储。tasks.json 损坏时不会自动清空，需用户从本地备份恢复。第一阶段一张纯 Prompt 图片的实际验证已成功；真实参考图上传、不同页面版本、模型选择和多任务执行尚未全面实测，遇到不确定结果保持待确认并只恢复收集。
