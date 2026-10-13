# Local change inventory and review

Work branch: `codex/open-source-readiness`, baseline `dff8a2c`. The user subsequently authorized committing, pushing and opening a pull request for these changes. Tag, Release, repository settings and community posts remain separate approval decisions. This preparation inventory includes all new public files; private runtime artifacts/caches are excluded.

## Main changes

- P0: English homepage/Chinese version, truthful historical evidence, portable consent-scoped Skill, explicit install/update/migration, portable Edge launcher and opt-in sensitive diagnostics.
- P1: Offline CI definition, real local checks, contribution/security/templates, demo recording guide and v0.1.0 draft/checklist.
- P2: Manual metadata, reviewed promotion candidates/rules, introduction drafts and verifiable search methods; no measured ranking improvement claimed.
- Later explicit live-test exception: serial Q01–Q03 trial, refusal stop/human-approved skip, verified Q03 cat timing; no refused-prompt retry. Future samples use cats. Original experiment prompts/snapshots and K01–K03 output hashes remain intact.

## Key actual diff excerpts

The complete local diff is reviewable in Codex/Git, including installer/launcher boundaries. These are source excerpts from the implemented changes, not pseudo-code claims:

```diff
-        print(json.dumps({"images": images, "headings":main.get_by_role('heading').all_text_contents(),
-                          "current_conversation_text": main.inner_text()[:3000]},
-                         ensure_ascii=False, indent=2))
+        result = {'images': images, 'headings':main.get_by_role('heading').all_text_contents()}
+        if args.include_conversation_text:
+            result['current_conversation_text'] = main.inner_text()[:3000]
+        print(json.dumps(result, ensure_ascii=False, indent=2))
+    if args.screenshot:
```

```diff
         if galleries.count() == 0:
+            completed = main.locator('[data-talvt-turn-state="complete"]')
+            if completed.count() == 1 and REFUSAL.search(completed.nth(0).inner_text()):
+                raise TaskError('platform_refusal: completed text response, no image; do not rewrite/resubmit')
             return None
```

## Changed / added files

43 public files modified/added; LICENSE and dependency requirement files were reviewed and retained.

- [.github/ISSUE_TEMPLATE/bug_report.yml](../.github/ISSUE_TEMPLATE/bug_report.yml)
- [.github/ISSUE_TEMPLATE/config.yml](../.github/ISSUE_TEMPLATE/config.yml)
- [.github/ISSUE_TEMPLATE/feature_request.yml](../.github/ISSUE_TEMPLATE/feature_request.yml)
- [.github/workflows/ci.yml](../.github/workflows/ci.yml)
- [.gitignore](../.gitignore)
- [CHANGELOG.md](../CHANGELOG.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [README.en.md](../README.en.md)
- [README.md](../README.md)
- [README.zh-CN.md](../README.zh-CN.md)
- [SECURITY.md](../SECURITY.md)
- [SKILL.md](../SKILL.md)
- [docs/DEMO_RECORDING.md](../docs/DEMO_RECORDING.md)
- [docs/GITHUB_SETTINGS.md](../docs/GITHUB_SETTINGS.md)
- [docs/HISTORICAL_EXPERIMENTS.md](../docs/HISTORICAL_EXPERIMENTS.md)
- [docs/LOCAL_CHANGE_SUMMARY.md](../docs/LOCAL_CHANGE_SUMMARY.md)
- [docs/OPTIMIZATION.md](../docs/OPTIMIZATION.md)
- [docs/PROJECT_AUDIT.md](../docs/PROJECT_AUDIT.md)
- [docs/PROMOTION_PLAN.md](../docs/PROMOTION_PLAN.md)
- [docs/QUEUE_TRIAL.md](../docs/QUEUE_TRIAL.md)
- [docs/REFERENCE_REVIEW.md](../docs/REFERENCE_REVIEW.md)
- [docs/RELEASE_CHECKLIST.md](../docs/RELEASE_CHECKLIST.md)
- [docs/RELEASE_NOTES_v0.1.0.md](../docs/RELEASE_NOTES_v0.1.0.md)
- [docs/RELEASE_READINESS.md](../docs/RELEASE_READINESS.md)
- [docs/RISKS.md](../docs/RISKS.md)
- [docs/SETUP.md](../docs/SETUP.md)
- [docs/TEST_RESULTS.md](../docs/TEST_RESULTS.md)
- [docs/USAGE.md](../docs/USAGE.md)
- [docs/assets/README.md](../docs/assets/README.md)
- [llms.txt](../llms.txt)
- [prompt.txt](../prompt.txt)
- [prompts/example.md](../prompts/example.md)
- [prompts/prompt.txt](../prompts/prompt.txt)
- [scripts/audit_public.py](../scripts/audit_public.py)
- [scripts/check_docs.py](../scripts/check_docs.py)
- [scripts/framebridge.py](../scripts/framebridge.py)
- [scripts/inspect_web.py](../scripts/inspect_web.py)
- [scripts/install_skill.py](../scripts/install_skill.py)
- [scripts/start_edge.ps1](../scripts/start_edge.ps1)
- [scripts/web_chatgpt.py](../scripts/web_chatgpt.py)
- [tests/test_browser_fixture.py](../tests/test_browser_fixture.py)
- [tests/test_edge_launcher.py](../tests/test_edge_launcher.py)
- [tests/test_public_setup.py](../tests/test_public_setup.py)

## Evidence and next actions

[Release readiness](RELEASE_READINESS.md) contains actual local results and pending remote/fresh-user checks. [Queue trial](QUEUE_TRIAL.md) contains exact observed outcomes and measurement limitations. [GitHub settings](GITHUB_SETTINGS.md) provides fields to apply manually; [release checklist](RELEASE_CHECKLIST.md) lists review, CI, demo and publication gates. The existing installed maintainer Skill and browser login/profile were not migrated/changed by this publication work; source Skill updates are separate from installation.
