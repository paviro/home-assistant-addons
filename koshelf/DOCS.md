# KoShelf setup

## Sidebar

1. Put books and KOReader metadata under `/share` or `/media`.
2. Set `library_path` to one or more folders, or set `statistics_db` to a list of
   KOReader `statistics.sqlite3` files. The existing single `database_path` setting
   is also supported. At least one library or statistics source is required.
3. Start KoShelf, click **Open Web UI**, and enable **Show in sidebar**.

Home Assistant authenticates sidebar requests. All authenticated HA users can
access the same library by default, including any enabled writeback features.
There are no separate personal libraries or per-user editing roles.

To restrict access, set `allowed_ha_user_ids` to the exact IDs of permitted
Home Assistant users. An empty list permits all authenticated users. Obtain
IDs from Home Assistant's user administration or authenticated user API. IDs
are 32 lowercase hexadecimal characters, not display names or usernames.
A denied or missing identity receives HTTP 403. Changing the list requires a restart.
The sidebar may still be visible to users excluded by this allowlist.

## Access settings

| Setting | Default | Behavior |
| --- | --- | --- |
| `direct_access_enabled` | `false` | Turn password-protected direct access on or off. Home Assistant sidebar access remains available. |
| `allow_insecure_http` | `false` | With direct access enabled, allow plain HTTP on a trusted LAN. Passwords and session cookies are unencrypted. |
| `direct_url` | empty | HTTPS origin of the direct reverse proxy, for example `https://books.example.com`; no paths. Required when HTTP is disabled. |
| `trusted_proxies` | `[]` | Exact addresses/CIDRs of direct-access TLS proxies. These proxies may assert client address and HTTPS scheme; this never grants login. |
| `allowed_ha_user_ids` | `[]` | Optional allowlist for sidebar access. |
| `reset_password` | `false` | Generate a replacement password and revoke sessions. The flag is cleared only after Supervisor confirms persistence. |

For an explicit sidebar-only setup:

```yaml
library_path:
  - /share/books
direct_access_enabled: false
allowed_ha_user_ids: []
```

### Optional direct HTTPS access

1. Set `direct_access_enabled: true`, `allow_insecure_http: false`, and `direct_url` to
   the external HTTPS origin.
2. Put only the TLS proxy's addresses in `trusted_proxies`. Do not trust client
   networks or all addresses. The proxy must overwrite forwarding headers.
3. In Nginx Proxy Manager, use forwarding scheme **http** and port **38492**;
   public HTTPS terminates at the proxy. Keep the `38492/tcp` mapping in Home
   Assistant's Network settings (mapped by default; nothing listens on it unless direct access is enabled).
4. Configure the TLS proxy to forward to that port, preserve the external Host,
   and set `X-Forwarded-Proto: https` and the actual client address in
   `X-Forwarded-For`. Serve KoShelf at `/` on its own hostname.
5. Restart and open the direct HTTPS address. Sign in with KoShelf's password.

**Nginx Proxy Manager add-on:** it runs on Home Assistant's internal network, so
trust that network and point the proxy host at the add-on:

```yaml
direct_access_enabled: true
direct_url: https://books.example.com
trusted_proxies:
  - 172.30.32.0/23
```

In Nginx Proxy Manager, forward `http` to your Home Assistant IP (or the add-on
hostname shown on its Info page) on port `38492`, enable Websockets support and
SSL. Its default headers already set Host, `X-Forwarded-For` and
`X-Forwarded-Proto`. Trusting this network lets other add-ons assert a client
address or scheme too; that never grants a login.

Requests that do not arrive through a configured proxy with HTTPS indicated,
using the configured Host, are rejected when LAN HTTP is disabled. The add-on
itself does not terminate TLS or provision certificates.

For trusted LAN HTTP, explicitly set `direct_access_enabled: true` and
`allow_insecure_http: true`, keep the network mapping, and open
`http://HOME_ASSISTANT_IP:38492`. Use HTTPS for access over untrusted networks.

KoShelf generates its initial direct-login password once and prints it in the
add-on log. Preserve it securely, or use `reset_password` to replace it.
Password and session management are available through direct login. Sidebar
login never issues a portable KoShelf session and cannot manage these credentials.

## Upgrading an existing installation

Update the existing `koshelf` add-on in the existing repository; do not uninstall.
The slug and `/data` layout stay unchanged. Existing library settings, password
hashes, and session data are retained.

When upgrading from the old access settings, the add-on migrates them once to
the **Direct access** switch:

- Old `auto` (or no mode) with `enable_auth: true`: turn direct access and
  **Allow plain HTTP** on, preserving the existing authenticated connection.
- Old `auto` with authentication off: leave direct access off.
- Old `enabled` or `disabled`: preserve that choice and the HTTP setting.

The migration saves the new settings through Supervisor and removes the retired
`direct_access` and `enable_auth` options. Passwords, sessions, trusted proxies,
and the `38492` host-port mapping are retained. If saving fails, startup stops
and retries on the next start without changing credentials.

New installations default to sidebar-only access. After the first startup,
**Direct access** appears as an on/off switch in configuration; before then it
is available under optional settings. No direct listener starts until enabled.

## Library and display settings

| Setting | Default | Meaning |
| --- | --- | --- |
| `library_path` | `[]` | Book/comic folders; each becomes a separate `--library-path`. |
| `database_path` | empty | KOReader statistics database. |
| `statistics_db` | `[]` | Statistics databases to merge across devices. Combined with `database_path`; identical paths are passed once. |
| `kobo_db` | empty | Kobo database for extensionless kepub discovery; requires a library. |
| `docsettings_path` | empty | Separate KOReader docsettings folder; requires a library. |
| `hashdocsettings_path` | empty | Hashed metadata folder; requires a library. Upstream determines metadata precedence. |
| `document_metadata_folder` | `doc` | Match KOReader's book metadata location: `doc` (adjacent), `dir` (docsettings), or `hash` (hashdocsettings). Controls custom metadata and cover lookup/writeback. |
| `archive_enabled` | `true` | Preserve missing books with saved metadata and covers. Disabled: hide archives and suspend preservation/cleanup; existing saved files remain untouched. |
| `archive_retention_days` | `"30"` | Retain saved files this many days after an archived entry is removed. `"0"` deletes immediately; `forever` retains indefinitely. |
| `include_unread` | `true` | Include supported files without reading metadata. |
| `include_all_stats` | `false` | Include statistics beyond the configured library. |
| `title` | empty | Use KoShelf's default title or supply a custom one. |
| `language` | `en_US` | Full locale such as `de_DE`; two-letter codes are rejected. |
| `timezone` | empty | Optional IANA timezone, otherwise upstream local time. |
| `heatmap_scale_max` | `auto` | Maximum heatmap intensity, such as `1h`. |
| `day_start_time` | empty | Logical day boundary, such as `04:00`. |
| `min_pages_per_day` | empty | Minimum pages to include a day's statistics. |
| `min_time_per_day` | `30s` | Minimum daily reading time. |
| `enable_writeback` | `false` | Permit supported edits to KOReader metadata. Applies to all allowed users. |
| `enable_library_management` | `false` | Permit all authorized users to remove archived entries. Requires archive preservation. Original books and sidecars remain untouched. |
| `ignore_stable_page_metadata` | `false` | Ignore stable-page metadata when computing statistics. |
| `debug_log` | `false` | Enable upstream debug logging for troubleshooting. |

All supplied source paths must be reachable within the `/share` or `/media`
mounts. Values are passed as argument arrays, never executed as shell commands.

For statistics from multiple devices:

```yaml
statistics_db:
  - /share/kobo/statistics.sqlite3
  - /share/boox/statistics.sqlite3
```

Archive retention starts when an archived entry is explicitly removed; missing
books do not expire automatically. Re-enabling archives resumes cleanup, including
retired files whose retention expired while archives were disabled. With archives
disabled, configured library folders must be available at startup. Restart the
add-on after changing these settings.

## Storage and backups

Home Assistant manages `/data` privately for this add-on. It contains KoShelf's
databases, credentials, sessions, and cached/generated files. Include the add-on
in backups. Cold backups stop it while capturing this state.

Books, statistics databases, and KOReader sidecars under `/share` or `/media`
need their own backup coverage; selecting only the add-on does not back up those
mounts. Restore both sources and add-on data when recovering the whole library.

## Troubleshooting

- **403 in sidebar:** check that Supervisor supplies a user ID, the ID is allowed,
  and the Ingress URL is used. Direct requests to port 8099 are deliberately denied.
- **Direct port unavailable:** enable `direct_access_enabled` and check that the host
  mapping was not removed in Network settings.
- **Login cookie does not stick:** verify HTTP/HTTPS mode, trusted TLS proxy addresses,
  external Host and scheme headers. Use the configured HTTPS origin.
- **Password reset did not clear:** check Supervisor API access. A completed reset
  is recorded in `/data` so an API failure does not repeatedly change the password.
- **Startup reports incompatible KoShelf:** the pinned release must include proxy
  integration. Do not bypass the compatibility check.
- **Scripts receive 403 on writes:** send `X-KoShelf-Request: 1`; do not enable
  permissive CORS. Authentication is still required separately.

Ingress does not provide a separately installable PWA. Use the direct HTTPS
address for standalone browser use.
