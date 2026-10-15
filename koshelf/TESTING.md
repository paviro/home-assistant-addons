# Validation

Verified locally on macOS on 2026-10-15:

- KoShelf: all 400 Rust tests passed during integration development. Following
  the user's CSRF adjustments and the cookie fix, all 33 auth tests and all three
  proxy tests passed. The frontend suite passed all 162 tests.
- Add-on: 17 Python unit tests passed, covering migration, proxy configuration,
  option validation, argument safety, reset retries, release candidates, and
  supervised shutdown when either service exits or receives a stop signal,
  multiple statistics sources, archive settings, and opt-in library management.
- Home Assistant's AwesomeVersion confirms `2026.10.0.1 > 2026.10.0`.
  The `-1` spelling is deliberately not used: it sorts below the existing release.
- YAML, option/schema/translation coverage, and architecture mappings validated.
- Real KoShelf and nginx 1.30.6 smoke tests passed: direct authentication,
  cookie revocation, LAN HTTP/HTTPS cookie flags, CSRF/preflight denial,
  proxy-auth trust separated from forwarded-IP trust, protected files,
  subpath HTML/assets/manifest, SSE, Supervisor-only Ingress, exact user
  allowlists, large request buffering, trusted TLS-proxy/Host enforcement,
  and stripping forged identity headers from direct requests.
- Repeated the integration test with the published 2026.10.0 macOS ARM binary
  and the add-on's generated command, including metadata location, archive
  retention, and library management options. All checks passed.
- Downloaded all four pinned Linux musl archives, verified their SHA-256 against
  both the manifest and published SHA256SUMS, and confirmed each contains an ELF
  executable. This does not replace container execution tests.

The cookie fix was amended into upstream integration commit `ce2d7e6`.
Later user commits tagged KoShelf 2026.10.0. Its release workflow succeeded,
including all four required Linux builds, and the published artifacts are pinned
in `upstream.json`. That add-on revision was 2026.10.0.1.

## Repeat local tests

```sh
python3 -m unittest discover -s tests -v
python3 -m venv /tmp/koshelf-validation
/tmp/koshelf-validation/bin/pip install -r tests/requirements.txt
/tmp/koshelf-validation/bin/python scripts/validate-metadata.py
python3 scripts/integration-smoke.py --binary /path/to/koshelf --nginx /path/to/nginx
```

The smoke test creates disposable data and random localhost ports. It first
tests the production Supervisor address restriction, then substitutes loopback
in a temporary nginx configuration to simulate authenticated Ingress requests.
It does not connect to a real Home Assistant instance or modify an existing library.

## Home Assistant verification

On 2026-10-15, the maintainer reported that Home Assistant Ingress works after
testing it on their installation. This confirms Ingress; the report does not
specify results for the other host checks below.

## Remaining release gates

Docker is not installed in this development environment. Container builds,
architecture execution, Home Assistant integration, companion-app behavior,
and backup/restore have **not** been verified here.

Before publishing the add-on update:

1. Run `sh scripts/check-release.sh` on a Docker host with QEMU/binfmt support.
   The script builds and executes the real integration test on amd64, aarch64,
   armv7 and i386. The CI release gate runs the same script.
2. Upgrade a backed-up existing HA installation, first with legacy authentication
   enabled and then with an unauthenticated fixture. Confirm preserved data and
   credentials, retained protected direct access, and closure of the old open port.
3. Test fresh sidebar-only setup, HA admin/non-admin accounts, and the user allowlist.
4. Test reader files, downloads, covers, SSE, edits with writeback enabled, browser
   refresh, and companion-app embedding under both local and remote HA origins.
5. Verify direct HTTPS through a trusted proxy, rejection from other peers,
   explicit LAN HTTP, password reset, restart, and shutdown of either child service.
6. Verify cold backup/restore, plus separate restoration of `/share` and `/media`.

Do not treat an unexecuted container or HA check as a passing result.

## Access settings simplification (2026.10.0.2)

- All 24 Python tests pass, including legacy access migration, explicit on/off
  choices, retry after failed Supervisor saves, and preservation of secret references.
- Metadata, translations, schema coverage, and version ordering pass validation.
- Migration uses Supervisor's stored self-info options because its options.json
  writer strips keys removed from the schema before the add-on starts.
- Container execution and migration on a real Home Assistant host have not been
  tested for this revision. The earlier maintainer Ingress confirmation does not
  cover these new migration changes.
