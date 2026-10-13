# v0.1.0 publication checklist

Local preparation does not authorize publication. Check boxes only with evidence.

- [ ] Review all local changes and approve the exact commit/source tree.
- [ ] Public/history scan and ignore checks pass; no private image/log/profile/URL/credential included. Decide Git author privacy for future commits without silently rewriting history.
- [ ] Compile, core tests, mocked browser tests, documentation links and Skill validation pass; retain actual results/skips/failures.
- [ ] Review minimal CI permissions and pinned actions/dependencies; approve git push separately.
- [ ] Run GitHub Actions on the approved commit. Windows/browser jobs and proposed Python/OS versions succeed; update evidence, not guessed badges.
- [ ] Another fresh user/machine verifies clone, consent-gated setup, manual login, Skill install/move/update and supported UI. Live generation requires separate test consent.
- [ ] Review all terms/security disclosures and supported/untested scope.
- [ ] Approve a real redacted demo and its media rights; absent demo stays explicitly pending.
- [ ] Apply GitHub Description/Topics and community/security settings manually; no false metrics or affiliation.
- [ ] Finalize CHANGELOG and Release Notes based on evidence.
- [ ] Obtain explicit authorization for Tag and Release; verify name v0.1.0 is not already used before acting.
- [ ] Build artifacts only from the approved Git source tree, not the working directory containing private runtime files; record checksums. Do not include installed Skill paths/backups.
- [ ] Publish only after approval; check download/README instructions against actual published assets.
- [ ] Recheck community/list rules and separately approve each announcement/listing PR; remain available for real feedback.

The user separately approved a repository commit/push/PR after local preparation. Tag, Release and promotion still require separate approval. See [RELEASE_READINESS.md](RELEASE_READINESS.md) for what is complete and what remains pending.
