# 参考项目审查

> 这是固定第三方版本的历史静态审查，不是安全认证。结尾“尚未验证”描述当时阶段；后续有限实测见 [HISTORICAL_EXPERIMENTS.md](HISTORICAL_EXPERIMENTS.md)，当前就绪状态见 [RELEASE_READINESS.md](RELEASE_READINESS.md)。未运行这些项目。

审查日期：2026-10-13。通过 GitHub API 获取提交树，再读取固定提交的原始源文件；只读审查，没有运行仓库脚本、安装这些仓库、启动服务或复制其实现。下面是范围有限的静态审查，不能作为全面安全认证。

| 项目与固定提交 | Windows / 可见 Chrome | Prompt / 参考图 | 完成 / 保存 | 判断 |
| --- | --- | --- | --- | --- |
| [Grey-G/chatgpt-imagegen](https://github.com/Grey-G/chatgpt-imagegen/tree/ba2ce7a5d9c66f19dbb7f5b00576bfb62e3936db) | Skill 使用 Codex 浏览器能力，含 Windows 示例；本地 helper 为 Python | helper 寻找 txt/md 等文件、读取 Prompt；Skill 指导 UI 上传/粘贴 | 观察新图、生成状态和 UI；文件数量/尺寸校验；资源导出与 CDP 回退 | 最贴近需求，参考工作流；不采纳 CDP 资源提取、自动重发、多组并发 |
| [yxhpy/playwright-openai-plugin](https://github.com/yxhpy/playwright-openai-plugin/tree/4b746eae68ab87c2b9e18eb44488f35682d554a0) | Node ≥20、标准 Playwright；显式 Windows Chrome 路径；可见受管 Chrome / CDP | CLI 接受 Prompt 和文件，setInputFiles 上传；包含本地 job 状态 | 新产物计数 + generating 状态；collect 在页面内 fetch(src) 后提取 base64 | 参考 submit/wait/collect 拆分和超时不重发；不直接复用下载实现或整个插件 |
| [StaticB1/browser-llm-api](https://github.com/StaticB1/browser-llm-api/tree/047131f023c1c1f590730de72e84b7c7fcebbd0b) | Python；nodriver；主部署围绕 Linux、Xvfb、systemd；可见显示模式 | OpenAI 兼容 HTTP/MCP 层接收 Prompt / attachments；DOM/CDP 上传 | DOM稳定 + 网络/WS事件；图片提取与服务层结果输出 | 不采用：超出单人原型范围，且存在认证读取和私有接口访问 |

## Grey-G 的具体参考点

已读 `SKILL.md`、`scripts/prepare_materials.py`、`agents/openai.yaml` 和 README。helper 可以做文件发现，但存在多个候选时会优先浅层与排序靠前的文件。本项目要求显式 Prompt 路径与参考图清单，避免把不相关文件自动上传。采用 UTF-8 txt/md，保留原始字节和换行，不需要它的 RTF/RTFD 提取与 macOS textutil 分支。

该 Skill 第 167 行附近说明完成信号；第 225–238 行附近提供 `Page.getResourceContent` 回退。我们参考可见状态与保存后验证，不使用资源提取。它建议卡住后停止、重发短 Prompt 或创建备用对话，本项目改为 failed + needs_confirmation，恢复只下载已有结果。

仓库提交树未见 LICENSE，GitHub license 元数据也为空；不假定 README 标注或公开可访问意味着已取得代码复制许可。因此本项目没有复制它的 helper/Skill，参考的是流程设计。

## Playwright 插件的具体参考点

审查 `package.json`、`src/{browser,cdp,chat,images,jobs,discover,paths,cli}.js` 及主 Skill。`src/paths.js` 包含 Windows 路径，`browser.js` 默认可见并通过单独 user-data-dir 启动；原来普通 Chrome 不一定可直接接入。`images.js` 的 `setInputFiles`、`waitForImageArtifacts` 和超时不重发的组织方式有参考价值。

`images.js` 第 1245 行附近的下载使用页面 `fetch(src)`，不是正常 Download/Save 按钮事件；与我们的指定路线不同。已审查的核心文件未见直接导出 Cookie/Token 或调用 ChatGPT 图片模型私有接口的实现；这是局部结论，不覆盖其它发布工具与所有依赖。该提交树未见 LICENSE，不直接复制代码。

## browser-llm-api 的排除理由

审查 README、requirements、pyproject、login.py、gemini_bot.py、providers/base.py、providers/chatgpt.py、server.py 和 SECURITY.md。`login.py` 第 57 行附近读取 browser.cookies.get_all()；`providers/chatgpt.py` 第 463 行附近访问 `/api/auth/session` 取得 accessToken，随后携带 Bearer 访问 `/backend-api/conversation/...`。同文件还包含列表/历史操作及限流暂停重试。这些代码违反本项目明确的认证数据与私有接口约束，不能因为它们不是直接调用图片模型就采用。

它依赖 nodriver；[nodriver 官方仓库](https://github.com/ultrafunkamsterdam/nodriver) 将反检测列为核心目标。无论某次运行是否实际规避检测，本项目都不引入该依赖。Linux 服务与 HTTP 兼容层也没有必要迁移到这个 Windows 单任务助手。该项目为 MIT，但许可允许复用不等于功能符合本项目约束。

## 技术路线

复用成熟库：正常 Playwright 的 DOM 定位、标准文件输入和 download/save_as，Pillow 的格式/像素解码。新增代码只负责本地任务、明确的 UI 顺序与安全停止，不重建浏览器驱动、生成接口或认证体系。当前真实 ChatGPT UI 适配尚未验证；模拟 DOM 测试不能证明线上控件始终相同。
