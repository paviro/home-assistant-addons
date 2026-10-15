# KoShelf for Home Assistant

Browse your KOReader library, read books, explore highlights, and view reading
statistics from the Home Assistant sidebar.

- Home Assistant sign-in opens the shared library without another password.
- Optional direct access uses KoShelf's password authentication.
- An optional Home Assistant user-ID allowlist controls sidebar access.
- Library settings, passwords, sessions, and caches survive in-place updates.

This experimental rebuild pins KoShelf `2026.10.0` with proxy authentication and
subpath support. Container and real Home Assistant verification remain required
before publishing the add-on update. See [TESTING.md](TESTING.md).

Configure a library path such as `/share/books` or a statistics
database, start the add-on, choose **Open Web UI**, and enable **Show in sidebar**.
See the **Documentation** tab for setup, direct access, migration, and backups.
