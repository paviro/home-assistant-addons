# Upstream and release gate

KoShelf source: https://github.com/paviro/KoShelf (EUPL-1.2).
`upstream.json` records the pinned upstream version, release artifacts, and their
SHA-256 checksums. `config.yaml` records the add-on version. Consult these files
for the release being built.

Compatible upstream releases must support `--bind-address`, `--auth-proxy-peers`,
request-scoped proxy authentication, CSRF headers, and dynamic subpath support.
`integration_ready` permits builds against the pinned artifacts; it is not evidence
that container or Home Assistant validation has passed for a release.
Complete the following release checks before publishing the add-on update.

1. Confirm the upstream tag in `upstream.json`, its source commit, and release notes.
2. For future updates, run `python3 scripts/update-upstream.py --write` to pin the
   stable release and all four Linux musl archive checksums. Review the source diff.
3. Run `sh scripts/check-release.sh` with Docker and QEMU available. Each advertised
   architecture must build and pass the real-server/proxy smoke test.
4. On Home Assistant, verify Ingress with admin and non-admin users, the allowlist,
   direct HTTPS and LAN HTTP, reader/downloads, SSE, edits, upgrade, restart, and
   backup/restore. Test the companion app as well.
5. Record results in the update PR with the tested versions and environment, then
   publish the add-on update through the existing repository.

No upstream executable is patched. Installation verifies the pinned checksum,
extracts only the expected binary, and checks required CLI support. Incompatible
releases fail closed. The runtime performs an additional compatibility check.

The image uses the Alpine base images specified in `build.yaml`, with Python,
nginx, certificates, and timezone data installed by `Dockerfile`. The wrapper
uses Home Assistant's Docker init. Advertised architectures are listed in
`config.yaml` and must match the build images and upstream artifacts.
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
fourth numeric component for add-on-only revisions when needed. The next newer
upstream release returns to its exact three-component version.
