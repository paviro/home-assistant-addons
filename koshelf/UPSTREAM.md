# Upstream and release gate

KoShelf source: https://github.com/paviro/KoShelf (EUPL-1.2).
`upstream.json` records reviewed release artifacts and their SHA-256 checksums.
The current checksums were read from release `2026.10.0` on 2026-10-15.

The published release includes `--bind-address`, `--auth-proxy-peers`,
request-scoped proxy authentication, CSRF headers, and dynamic subpath support.
`integration_ready` now enables builds against these pinned artifacts. This flag
records upstream compatibility, not completion of container or HA validation.
Complete the following release checks before publishing the add-on update.

1. Confirm the reviewed upstream tag and release notes. The current tag is
   `2026.10.0`, source commit `855c200a1d5e65b86cb5dcec6e395e85ec3921a9`.
2. For future updates, run `python3 scripts/update-upstream.py --write` to pin the
   stable release and all four Linux musl archive checksums. Review the source diff.
3. Run `sh scripts/check-release.sh` with Docker and QEMU available. Each advertised
   architecture must build and pass the real-server/proxy smoke test.
4. On Home Assistant, verify Ingress with admin and non-admin users, the allowlist,
   direct HTTPS and LAN HTTP, reader/downloads, SSE, edits, upgrade, restart, and
   backup/restore. Test the companion app as well.
5. Record results in TESTING.md, then publish the add-on update through the existing
   repository.

No upstream executable is patched. Installation verifies the pinned checksum,
extracts only the expected binary, and checks required CLI support. Incompatible
releases fail closed. The runtime performs an additional compatibility check.

The image uses Alpine 3.23 with Python, nginx, certificates and timezone data.
The wrapper uses Home Assistant's Docker init instead of requiring the former
bashio/s6 image. This preserves all four architectures without relying on current
Home Assistant base-image builds, which now advertise only amd64 and aarch64.
Alpine packages are resolved at build time; this is not a byte-for-byte reproducible
image. Both base-image and package security updates need maintainer review.

## Automated updates

The repository workflow runs daily and on demand. It discovers a newer stable
KoShelf release, validates all architecture assets/checksums, updates the pinned
manifest and add-on version, and runs unit tests plus all container smoke tests
before opening a PR. It never auto-merges or publishes a release.

Enable GitHub Actions and allow GitHub Actions to create pull requests in the
repository settings. The workflow uses the repository GITHUB_TOKEN; no PAT is
required. Because PRs created with that token do not normally trigger further
workflows, the update workflow runs the complete build/smoke checks itself before
creating the PR. Human PR changes also run the regular CI workflow.

New upstream releases use the exact KoShelf version for the add-on. Reserve a
fourth numeric component for add-on-only revisions when needed. The existing
`2026.10.0.2` includes these add-on-only changes; the next newer upstream
release returns to the three-component version.
