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

[![Open your Home Assistant instance and show the dashboard of an add-on.](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=5d189d71_koshelf&repository_url=https%3A%2F%2Fgithub.com%2Fpaviro%2Fhome-assistant-addons)

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

- **docsettings_path**: Path to KOReader's docsettings folder for users who store metadata separately
  - Example: `/share/koreader/docsettings`
  - Requires `books_path` to be set
  - Mutually exclusive with `hashdocsettings_path`
  - Use this if your KoReader metadata is stored in a separate docsettings folder

- **hashdocsettings_path**: Path to KOReader's hashdocsettings folder for users who store metadata by content hash
  - Example: `/share/koreader/hashdocsettings`
  - Requires `books_path` to be set
  - Mutually exclusive with `docsettings_path`
  - Use this if your KoReader metadata is stored using content hash-based naming

- **include_unread**: Include unread books (EPUBs without KoReader metadata) in the generated site
  - Default: `false`
  - Set to `true` to show all EPUB files, even those you haven't opened in KoReader yet

- **title**: Custom site title
  - Default: `"KoShelf"`
  - Example: `"My Reading Library"`
  - Sets the title displayed on your KoShelf site

- **heatmap_scale_max**: Maximum value for heatmap color intensity scaling
  - Default: `"auto"`
  - Examples: `"auto"`, `"1h"`, `"1h30m"`, `"45min"`
  - Values above this will still be shown but use the highest color intensity
  - `"auto"` enables automatic scaling based on your data

- **day_start_time**: Logical day start time in `HH:MM`
  - Default: `"00:00"`
  - Determines when a new logical day begins for statistics

- **timezone**: IANA timezone name used to interpret timestamps
  - Default: system local timezone
  - Examples: `"Australia/Sydney"`, `"America/New_York"`, `"Europe/Berlin"`

- **min_pages_per_day**: Minimum required pages read per day to be counted in statistics
  - Example: `10`
  - Optional integer value
  - Days with fewer pages read will not be counted in statistics

- **min_time_per_day**: Minimum required reading time per day to be counted in statistics
  - Examples: `"15m"`, `"1h"`, `"30m"`
  - Optional duration value
  - Days with less reading time will not be counted in statistics

**Note**: If both `min_pages_per_day` and `min_time_per_day` are provided, a day is counted if either condition is met.

### Example Configuration

```yaml
books_path: /share/books
database_path: /share/koreader/statistics.sqlite3
docsettings_path: /share/koreader/docsettings
include_unread: true
title: "My Reading Library"
heatmap_scale_max: "auto"
day_start_time: "04:00"
timezone: "Australia/Sydney"
min_pages_per_day: 10
min_time_per_day: "15m"
```

## File Structure Expected

KoShelf supports the three ways KOReader can store metadata:

### Option 1: Metadata alongside books (Default, Recommended)

By default, KOReader creates `.sdr` folders next to each book file:

```
/share/books/  (configured as books_path)
├── Book Title.epub
├── Book Title.sdr/
│   └── metadata.epub.lua
├── Another Book.epub
├── Another Book.sdr/
│   └── metadata.epub.lua
└── ...
```

The `.sdr` directories are automatically created by KoReader when you read books and make highlights/annotations.

**Configuration**: Just set `books_path` - no additional paths needed.

### Option 2: Hashdocsettings

If you select "hashdocsettings" in KOReader settings, metadata is stored in a central folder organized by content hash with two-character subdirectories:

```
/share/books/
├── Book Title.epub
├── Another Book.epub
└── ...

/share/koreader/hashdocsettings/  (configured as hashdocsettings_path)
├── 57/
│   └── 570615f811d504e628db1ef262bea270.sdr/
│       └── metadata.epub.lua
└── a3/
    └── a3b2c1d4e5f6...sdr/
        └── metadata.epub.lua
```

**Configuration**: Set both `books_path` and `hashdocsettings_path`.

### Option 3: Docsettings

If you select "docsettings" in KOReader settings, KOReader mirrors your book folder structure in a central folder:

```
/share/books/
├── Book Title.epub
├── Another Book.epub
└── ...

/share/koreader/docsettings/  (configured as docsettings_path)
└── home/
    └── user/
        └── Books/
            ├── Book Title.sdr/
            │   └── metadata.epub.lua
            └── Another Book.sdr/
                └── metadata.epub.lua
```

> [!NOTE]
> Unlike KOReader, KOShelf matches books by filename only, since the folder structure reflects the device path (which may differ from your local path). If you have multiple books with the same filename, KOShelf will show an error - use hashdocsettings or the default book folder method instead.

**Configuration**: Set both `books_path` and `docsettings_path`.

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
