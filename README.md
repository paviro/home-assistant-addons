# KoShelf Home Assistant Addon

A Home Assistant addon that runs [KoShelf](https://github.com/paviro/KOShelf) - a beautiful static website generator for your KoReader library, showcasing your ebook collection with highlights, annotations, and reading progress.

## About

This addon packages the KoShelf Rust CLI tool as a Home Assistant addon, making it easy to run KoShelf on your Home Assistant instance. It automatically downloads the appropriate KoShelf binary for your system architecture and runs it in web server mode.

## Features

- 📚 **Book Library Overview**: Displays your currently reading, completed and unread books (EPUBs only!)
- 🎨 **Modern UI**: Beautiful design powered by Tailwind CSS with clean typography and responsive layout
- 📝 **Annotations & Highlights**: Shows all your KoReader highlights and notes with elegant formatting
- 📖 **Book Details**: Individual pages for each book with metadata and organized annotations
- 📊 **Reading Statistics**: Track your reading habits with detailed statistics including reading time, pages read, activity heatmaps, and weekly breakdowns
- 📈 **Per-Book Statistics**: Detailed statistics for each book including session count, average session duration, reading speed, and last read date
- 🔍 **Search & Filter**: Search through your library by title, author, or series, with filters for reading status
- 🚀 **Web Interface**: Runs as a web server accessible through Home Assistant
- 📱 **Responsive**: Optimized for desktop, tablet, and mobile with adaptive grid layouts

## Installation

Click the Home Assistant My button below to open the add-on on your Home Assistant instance.

[![Open your Home Assistant instance and show the dashboard of an add-on.](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=koshelf&repository_url=https%3A%2F%2Fgithub.com%2Fpaviro%2FKOShelf-home-assistant-addon)

1. Click the "Install" button to install the add-on.
2. Configure the addon (see Configuration section below)
3. Start the addon
4. Access your library at `http://homeassistant.local:38492` (or your Home Assistant IP with port 38492)

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

## Supported Data

### From EPUB Files
- Book title, authors, description
- Cover image, language, publisher
- Series information (name and number)
- Identifiers (ISBN, ASIN, Goodreads, DOI, etc.)
- Subjects/Genres

### From KoReader Metadata
- Reading status (reading/complete)
- Highlights and annotations with chapter information
- Notes attached to highlights
- Reading progress percentage
- Rating (stars out of 5)
- Summary note

### From KoReader Statistics Database
- Total reading time and pages
- Weekly reading statistics
- Reading activity heatmap
- Per-book reading sessions and statistics
- Reading speed calculations
- Session duration tracking
