# Release readiness — local preparation, not publication

Status: **v0.1.0 preparation completed locally; remote CI/Tag/Release/promotion pending**. No passing CI badge is warranted by local tests. Work is on `codex/open-source-readiness`; the user subsequently authorized a commit, push and pull request. That approval does not authorize a Tag, Release or promotion.

## Complete locally

- English homepage and Chinese README, clone-first setup, current-user consent and narrow support claims.
- Portable public Skill and explicit managed/legacy install/move update; no login/CDP/generation permission inherited.
- Edge discovery/overrides, consent flag, DryRun and separate-profile boundaries; loopback launch argument and client endpoint restrictions.
- Offline workflow definition with pinned actions, contents:read, no persisted checkout credentials, no secrets and isolated mocked browser contexts.
- Contributor/security/issue files, demo plan, v0.1.0 notes/checklist, manual metadata and promotion drafts.
- Historical K01/K02/K03/test evidence preserved and explicitly separated from current-user state.

## Actual local validation — 2026-10-13

Environment: Windows 10 build 19045, Python 3.11.11, Pillow 12.3.0, Playwright 1.63.0, installed Edge used only in isolated headless fixture contexts for the offline suite.

| Check | Actual result |
| --- | --- |
| Full offline suite, `FRAMEBRIDGE_FIXTURE_BROWSER=msedge` | **58 passed, 0 failed, 0 skipped, 35.219 s**: 19 existing core/boundary cases, 25 browser fixtures, 9 setup/audit/doc cases, 5 Windows launcher safety cases |
| `python -m compileall -q scripts tests` | Exit 0 |
| `python scripts/check_docs.py` | 28 Markdown files: relative links, Chinese anchors, fences and Skill frontmatter pass; external links are not fetched by this check |
| `python scripts/audit_public.py --history` | No findings in 57 public working files and 30 unique reachable local Git blobs; heuristic, not a security certification |
| Skill creator's local validator | Valid source Skill; installer tests use temporary destinations, not the maintainer's installed entry |
| Four GitHub YAML files | Parsed locally; Push/PR and contents:read structure checked; no remote execution implied |
| PowerShell parser and launcher `-DryRun -Port 49333` | No parser errors; WouldLaunch=false; no browser/profile created |
| Launcher safety cases | Missing consent, default/in-checkout profiles and occupied port rejected; dry run does not launch |
| `git diff --check` | Exit 0; local Git line-ending conversion warnings are not test failures |
| Ignore protections | 10 representative runtime/private paths checked with `git check-ignore --no-index`; all ignored |

The offline browser suite fulfills the fixture page request locally, aborts other page requests and blocks service workers. It never uses the existing CDP browser, credentials or ChatGPT servers. Launcher tests use an inert executable file and never launch it. A dry run is not an actual browser launch/login. Tests do not establish every live UI/platform/permission case. The dependency versions above are observations, not lockfile/reproducible-build guarantees.

Separately, the user explicitly authorized a real serial trial after the original publication-only request: [Q01/Q02/Q03 evidence](QUEUE_TRIAL.md). Q01/Q03 passed image decoding/hash checks; Q02 refused and stopped; the user closed it and authorized Q03. Original K01/K02/K03 output hashes were rechecked without change. The existing debugging listener was observed at 127.0.0.1 only; that observation does not prove all future launches bind correctly.

## Pending validation

Later same-conversation work on `codex/same-chat-batch` is recorded in [SAME_CHAT_BATCH.md](SAME_CHAT_BATCH.md): 65 local full-suite tests passed in 46.390 s, then two additional legacy/recovery fixtures passed targeted runs. A separately user-authorized two-image cat sequence completed in one conversation in 88.469 s. The user subsequently approved submitting this feature as a PR; remote CI results must be observed on its exact revision, since earlier CI success does not validate it. Original validation above remains historical evidence for the publication-preparation scope.

- Actual GitHub Actions jobs after an approved push; Windows/Linux/Python matrix is a proposed scope, not demonstrated remote compatibility.
- Fresh-user/new-machine clone, browser policy/install variants, Codex discovery and Skill migration in a real new environment.
- Dependency vulnerability/advisory review beyond a secret heuristic; runtime package ranges are not a reproducible security guarantee.
- Multiple live reference uploads/JPG/WebP/identity behavior beyond the later single-PNG edit trial, Chrome/other UI language versions and general batch behavior beyond specific observations.
- Approved, real, redacted demo media; present directory contains instructions only.

## Pending manual / publication

Later work on `codex/reference-image-edit`: [reference/edit evidence](REFERENCE_IMAGE_EDIT.md) records 78 offline tests passed in 71.899 s and one real PNG edit uploaded/downloaded through normal controls. It stopped once before Send for paragraph-rendering mismatch, then resumed the unchanged never-submitted draft without reuploading; actual Send count was one. The user subsequently authorized a repository commit/push/PR for this feature. Remote CI must be observed on its exact revision; earlier preparation/CI records do not validate it. Tag, Release and promotion remain separate decisions.

Review diff and privacy findings; decide author identity/settings; observe CI on the user-approved PR; enable/check private reporting; paste About Description/Topics; approve demo rights; review release notes; explicitly approve Tag/Release; approve each community post/list PR. Publication and metadata steps remain manual. gh was not logged in when checked; metadata fields are supplied in [GITHUB_SETTINGS.md](GITHUB_SETTINGS.md).

Follow [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md). No search-index improvement or release distribution has been measured; opening a PR does not demonstrate either.
