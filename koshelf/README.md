# KoShelf Home Assistant Addon

A Home Assistant addon that runs [KoShelf](https://github.com/paviro/KOShelf) - a beautiful static website generator for your KoReader library, showcasing your ebook collection with highlights, annotations, and reading progress.

## Configuration

### File Location Requirements

**Important**: This addon only has access to the `/media/` and `/share/` mount points. Your book files and KoReader statistics database **must** be located in one of these directories.

### Required Configuration

**At least one** (or both) of the following must be configured:

- **books_path**: Path to your folder containing EPUB files and KoReader metadata
  - Example: `/share/books` or `/media/books`
  - This should point to where your EPUB files and their corresponding `.sdr` folders are located
  - Required for book library functionality

- **database_path**: Path to the KoReader statistics.sqlite3 file for reading stats
  - Example: `/share/koreader/statistics.sqlite3` or `/media/koreader/statistics.sqlite3`
  - This enables detailed reading statistics, activity heatmaps, and session tracking
  - Required for statistics functionality

### Optional Configuration

- **include_unread**: Include unread books (EPUBs without KoReader metadata) in the generated site
  - Default: `false`
  - Set to `true` to show all EPUB files, even those you haven't opened in KoReader yet

### Example Configuration

```yaml
books_path: /share/books
database_path: /share/koreader/statistics.sqlite3
include_unread: true
```

## File Structure Expected

This addon expects your books to be organized like this:

```
/share/books/  (or your configured path)
├── Book Title.epub
├── Book Title.sdr/
│   └── metadata.epub.lua
├── Another Book.epub
├── Another Book.sdr/
│   └── metadata.epub.lua
└── ...
```

The `.sdr` directories are automatically created by KoReader when you read books and make highlights/annotations.

## Accessing the Web Interface

Once the addon is running, you can access your KoShelf library at:
- `http://homeassistant.local:38492`
- `http://[YOUR_HOME_ASSISTANT_IP]:38492`

The addon runs KoShelf in web server mode, which means it will automatically rebuild the site when your book files change.

### Recommended: Use with Nginx Reverse Proxy

For enhanced security, SSL support, and custom domain access, it's highly recommended to use this addon behind a reverse proxy. The [Nginx Proxy Manager addon](https://github.com/hassio-addons/addon-nginx-proxy-manager) provides an easy-to-use interface for setting up reverse proxies in Home Assistant.