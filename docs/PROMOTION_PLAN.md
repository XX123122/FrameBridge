# Discoverability and promotion plan — drafts only

Sources checked 2026-10-13. No listing PR, community post, moderator message, metadata write, Tag or Release is performed. The user subsequently authorized a repository commit/push/PR; promotion actions still need separate human approval. Recheck mutable community/list rules immediately before submission.

## First make the project usable

Complete [release gates](RELEASE_CHECKLIST.md), observe actual CI, review a real redacted demo, and obtain fresh-user feedback. Apply accurate [Description/Topics](GITHUB_SETTINGS.md) manually. A v0.1.0 Release should name supported/untested scope and point to the approved source tree. A topic or llms.txt does not guarantee indexing or AI recommendations.

## Awesome lists: fit and actual rules

| Candidate | Checked primary rules / decision |
| --- | --- |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills/blob/main/CONTRIBUTING.md) | Public working Skill with docs, author/org prefix, short description (at most 10 words), appropriate community category; **real community use required, newly created unproven Skills not accepted**. Relevant future fit, **defer now**: no independent community adoption is established. |
| [mxschmitt/awesome-playwright](https://github.com/mxschmitt/awesome-playwright/blob/main/CONTRIBUTING.md) | Contribution guide requires following its code of conduct and maintainer review; retrieved checklist is generic, not proof a ChatGPT wrapper is eligible. README includes automation/AI categories. Possible future fit after a release/demo; manually ask about category/eligibility only with approval. |
| [sindresorhus/awesome](https://github.com/sindresorhus/awesome/blob/main/pull_request_template.md) | Curates **Awesome lists**, not individual software; requires mature lists and rejects fully AI-generated submissions. Do **not** submit FrameBridge directly or manufacture a list/community to meet its rules. |
| [awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) | Describes hostable network services/web applications. FrameBridge is a local UI workflow depending on ChatGPT, not a self-hosted model/service; not a suitable claim. Its contribution URL retrieval was unavailable, so no submission readiness is asserted. |

Future short entry draft, only after actual adoption and eligibility review:

> XX123122/FrameBridge — Supervised local ChatGPT image tasks for Codex.

Do not submit AI-written text unchanged where a list disallows it. Maintainers should review/write their own final submission and substantiate every claim. No fake usage figures, automatic stars, reciprocal vote campaigns or spam.

## Communities

- **V2EX 分享创造 / developer discussion**: [official FAQ](https://www.v2ex.com/faq) welcomes original projects but rejects repetitive link搬运; choose the precise node, explain the implementation and limitations, and engage with concrete feedback. Recheck node-specific guidance. Do not mass cross-post.
- **Reddit r/opensource** is a candidate audience, not a confirmed permission. [Current spam policy](https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam) prohibits repetitive/unsolicited mass engagement and says to follow each community's rules. The fetched subreddit rules page did not expose usable rule text, so a human must check them/moderator expectations before posting. The older Reddit self-promotion wiki says it is no longer updated; do not treat its old percentage guideline as current sitewide permission.
- **Hacker News Show HN**: [official rules](https://news.ycombinator.com/showhn.html) expect something people can actually try, not a landing page/list; be available to discuss, disclose the required ChatGPT account/manual setup, and never solicit votes. Defer until fresh-user setup/demo evidence is ready. A code/update announcement alone is not guaranteed to meet the bar.

Terms-sensitive browser automation may be inappropriate for a community even if its topic fits. Disclose it; do not frame the project as an unlimited/free/official API or a restriction workaround.

## English introduction draft

> FrameBridge is an unofficial local ChatGPT browser image workflow for Windows and Codex. It preserves prompt files, uses a user-configured visible Edge session, sends one authorized request, downloads through normal page controls and verifies the saved image. It was developed with Codex-assisted work; local tests and narrow maintainer-authorized Chinese-UI trials are documented. New users configure/login/authorize themselves. It does not export authentication, call a paid model API, or bypass protection. Automated output collection has service-terms risk. I’m looking for reproducible, sanitized feedback on setup, recovery and documentation; reference uploads and wider UI compatibility are not comprehensively live-tested.

## 中文介绍草稿

> FrameBridge 是一个 Windows + Codex 的非官方本地 ChatGPT 网页图片流程工具：保留 Prompt，使用用户自己配置和登录的可见 Edge，单任务授权后只发送一次，通过正常按钮下载并验证文件。代码采用 Codex 辅助开发，本地测试和有限中文 UI 实测证据已公开。新用户仍需自行配置、登录和授权；不导出认证、不调用付费模型 API、不绕过保护。自动获取输出有服务条款风险。希望收集可复现的脱敏接入、恢复和文档反馈；参考图上传与更多界面版本尚未全面实测。

Drafts must be updated with the actual reviewed release/CI status before approval. Do not invent a released version, user count, official permission or performance guarantee.

## Verifiable search tests

After approved publication, maintain a dated manual log with engine, query, locale, signed-in/out state, result URL/title/snippet, and whether it accurately reflects supported/untested scope. Use a small set, not scripted mass queries:

```text
FrameBridge ChatGPT Codex
site:github.com/XX123122/FrameBridge FrameBridge
ChatGPT browser image generation automation Windows
Local ChatGPT image generation workflow
ChatGPT image generation with Codex
Playwright ChatGPT image download
Windows Codex image generation Skill
```

Check GitHub search, Google, Bing and an AI search tool separately. An absent result in one run does not prove deindexing; personalized results do not establish ranking gains. For AI search, verify the returned citation against the repo and check it does not call this official, unlimited or fully cross-platform. Keep screenshots free of account/search-history information. There is no measured search-visibility improvement yet; PR submission alone is not such evidence.

Google says crawl requests are not guarantees and are limited to URLs you manage ([Search Central](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl)). A GitHub repository owner does not control github.com's domain verification. Do not claim an indexing API submission for that domain. [Bing guidelines](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a) were checked but render through JavaScript in the retrieval tool; site verification/IndexNow would require a future owned site, not fabricated keys for github.com.

## Improve from real feedback

Prioritize reproducible installation/consent/recovery failures over popularity. Classify unsupported UI variants, fix narrow selectors with offline regressions, separate local/CI/live evidence, and update both READMEs. Ask consent before any new live test or media sharing. Track real resolved issues and independent setup reports; do not turn stars/downloads into manufactured quality evidence.
