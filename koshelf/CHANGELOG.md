# 2026.10.0.2

- Replace direct-access modes and the legacy authentication setting with one on/off switch.
- Automatically preserve existing direct-access and HTTP settings during migration.
- Remove the experimental badge after maintainer verification of Ingress.
- Rename the library management setting and clarify its current scope.
- Match the exact upstream version again on the next KoShelf update.

# 2026.10.0.1

- Update KoShelf to 2026.10.0 with checksum-pinned artifacts for all four architectures.
- Add authenticated Home Assistant sidebar access and an optional HA user allowlist.
- Keep optional direct access password-protected and isolated from sidebar identity.
- Preserve authenticated direct access during migration; close unauthenticated access.
- Add process supervision, health checks, cold backups, and reliable reset retries.
- Add checksum-pinned releases, compatibility gates, and tested upstream update PRs.
- Improve setup documentation and configuration descriptions.
- Expose multi-device statistics, custom metadata location, archive preservation,
  removal retention, and opt-in library management settings.
