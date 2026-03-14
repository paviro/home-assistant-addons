#!/usr/bin/with-contenv bashio

echo "Starting koshelf addon..."

# Get configuration from addon
BOOKS_PATH=$(bashio::config 'books_path')
INCLUDE_UNREAD=$(bashio::config 'include_unread')
INCLUDE_ALL_STATS=$(bashio::config 'include_all_stats')
DATABASE_PATH=$(bashio::config 'database_path')
DOCSETTINGS_PATH=$(bashio::config 'docsettings_path')
HASHDOCSETTINGS_PATH=$(bashio::config 'hashdocsettings_path')
HEATMAP_SCALE_MAX=$(bashio::config 'heatmap_scale_max')
DAY_START_TIME=$(bashio::config 'day_start_time')
TIMEZONE=$(bashio::config 'timezone')
TITLE=$(bashio::config 'title')
MIN_PAGES_PER_DAY=$(bashio::config 'min_pages_per_day')
MIN_TIME_PER_DAY=$(bashio::config 'min_time_per_day')
LANGUAGE=$(bashio::config 'language')
DEBUG_LOG=$(bashio::config 'debug_log')

# Set RUST_LOG if debug logging is enabled
if [ "$DEBUG_LOG" = "true" ]; then
    export RUST_LOG=debug
    echo "Debug logging enabled (RUST_LOG=debug)"
fi

# Build list of library paths (supports multiple values)
LIBRARY_PATHS=()
if bashio::config.has_value 'library_path'; then
    # library_path is an array in config.yaml; parse it into a bash array
    while IFS= read -r p; do
        if [ -n "$p" ] && [ "$p" != "null" ]; then
            LIBRARY_PATHS+=("$p")
        fi
    done < <(bashio::addon.config | jq -r '.library_path[]? // empty')
fi

# Backwards-compat: migrate books_path -> library_path if user hasn't set library_path
if [ ${#LIBRARY_PATHS[@]} -eq 0 ] && [ -n "$BOOKS_PATH" ] && [ "$BOOKS_PATH" != "" ]; then
    bashio::log.warning "Deprecated config 'books_path' detected; please migrate to 'library_path'. Using books_path as a single library path for now."
    LIBRARY_PATHS+=("$BOOKS_PATH")
fi

echo "Library paths: ${LIBRARY_PATHS[*]}"
echo "Include unread: $INCLUDE_UNREAD"
echo "Include all stats: $INCLUDE_ALL_STATS"
echo "Database path: $DATABASE_PATH"
echo "Docsettings path: $DOCSETTINGS_PATH"
echo "Hashdocsettings path: $HASHDOCSETTINGS_PATH"
echo "Heatmap scale max: $HEATMAP_SCALE_MAX"
echo "Day start time: $DAY_START_TIME"
echo "Timezone: $TIMEZONE"
echo "Title: $TITLE"
echo "Min pages per day: $MIN_PAGES_PER_DAY"
echo "Min time per day: $MIN_TIME_PER_DAY"
echo "Language: $LANGUAGE"
echo "Data path: /data (persistent)"

# Validate language code
if [[ "$LANGUAGE" =~ ^[a-zA-Z]{2}$ ]]; then
    echo ""
    echo "║"
    echo "║                                ⚠️  ERROR  ⚠️"
    echo "║"
    echo "║"
    echo "║  🚨 INVALID LANGUAGE CODE 🚨"
    echo "║"
    echo "║  You have configured a two-letter language code: '$LANGUAGE'"
    echo "║"
    echo "║  You must use a full locale code (e.g., 'en_US', 'de_DE')"
    echo "║  to ensure correct date formatting and regional settings."
    echo "║"
    echo "║  The application cannot start with this configuration."
    echo "║"
    echo "║"
    echo ""
    bashio::log.fatal "Invalid language code '$LANGUAGE' - full locale required (e.g., en_US)"
    bashio::exit.nok
fi

# Validate that at least one path is provided
if [ ${#LIBRARY_PATHS[@]} -eq 0 ] && [[ -z "$DATABASE_PATH" || "$DATABASE_PATH" == "" ]]; then
    echo ""
    echo "║"
    echo "║                                ⚠️  ERROR  ⚠️"
    echo "║"
    echo "║"
    echo "║  🚨 CONFIGURATION REQUIRED 🚨"
    echo "║"
    echo "║  At least ONE of the following must be configured:"
    echo "║"
    echo "║  📚 library_path   - One or more paths to your ebook and comic files"
    echo "║  📊 database_path  - Path to KoReader's statistics.sqlite3 file"
    echo "║"
    echo "║  Example configurations:"
    echo "║"
    echo "║  Option 1 - Library only:"
    echo "║    library_path:"
    echo "║      - /share/books"
    echo "║"
    echo "║  Option 2 - Statistics only:"
    echo "║    database_path: /share/koreader/statistics.sqlite3"
    echo "║"
    echo "║  Option 3 - Both (recommended):"
    echo "║    library_path:"
    echo "║      - /share/books"
    echo "║    database_path: /share/koreader/statistics.sqlite3"
    echo "║"
    echo "║  💡 Remember: Files must be under /media/ or /share/ directories!"
    echo "║"
    echo "║"
    echo ""
    bashio::log.fatal "KoShelf addon configuration error - see detailed message above"
    bashio::exit.nok
fi

# Start building command with port and persistent data path
# /data is the HA addon persistent directory — survives reboots and updates
COMMAND=(/usr/local/bin/koshelf --port 38492 --data-path /data)

# Add one or more --library-path flags
if [ ${#LIBRARY_PATHS[@]} -gt 0 ]; then
    for p in "${LIBRARY_PATHS[@]}"; do
        COMMAND+=(--library-path "$p")
    done
fi

# Add statistics-db if provided
if [ -n "$DATABASE_PATH" ] && [ "$DATABASE_PATH" != "" ]; then
    COMMAND+=(--statistics-db "$DATABASE_PATH")
fi

# Add optional --include-unread flag (only when library paths are provided)
if [ "$INCLUDE_UNREAD" = "true" ] && [ ${#LIBRARY_PATHS[@]} -gt 0 ]; then
    COMMAND+=(--include-unread)
fi

# Add optional --include-all-stats flag
if [ "$INCLUDE_ALL_STATS" = "true" ]; then
    COMMAND+=(--include-all-stats)
fi

# Add optional heatmap-scale-max if provided
if [ -n "$HEATMAP_SCALE_MAX" ] && [ "$HEATMAP_SCALE_MAX" != "" ]; then
    COMMAND+=(--heatmap-scale-max "$HEATMAP_SCALE_MAX")
fi

# Add optional day start time if provided
if [ -n "$DAY_START_TIME" ] && [ "$DAY_START_TIME" != "" ]; then
    COMMAND+=(--day-start-time "$DAY_START_TIME")
fi

# Add optional timezone if provided
if [ -n "$TIMEZONE" ] && [ "$TIMEZONE" != "" ]; then
    COMMAND+=(--timezone "$TIMEZONE")
fi

# Add optional docsettings-path if provided
if [ -n "$DOCSETTINGS_PATH" ] && [ "$DOCSETTINGS_PATH" != "" ]; then
    COMMAND+=(--docsettings-path "$DOCSETTINGS_PATH")
fi

# Add optional hashdocsettings-path if provided
if [ -n "$HASHDOCSETTINGS_PATH" ] && [ "$HASHDOCSETTINGS_PATH" != "" ]; then
    COMMAND+=(--hashdocsettings-path "$HASHDOCSETTINGS_PATH")
fi

# Add optional title if provided
if [ -n "$TITLE" ] && [ "$TITLE" != "" ]; then
    COMMAND+=(--title "$TITLE")
fi

# Add optional min-pages-per-day if provided
if [ -n "$MIN_PAGES_PER_DAY" ] && [ "$MIN_PAGES_PER_DAY" != "" ]; then
    COMMAND+=(--min-pages-per-day "$MIN_PAGES_PER_DAY")
fi

# Add optional min-time-per-day if provided
if [ -n "$MIN_TIME_PER_DAY" ] && [ "$MIN_TIME_PER_DAY" != "" ]; then
    COMMAND+=(--min-time-per-day "$MIN_TIME_PER_DAY")
fi

# Add optional language if provided
if [ -n "$LANGUAGE" ] && [ "$LANGUAGE" != "" ]; then
    COMMAND+=(--language "$LANGUAGE")
fi

echo "Running: ${COMMAND[*]}"

# Run koshelf
exec "${COMMAND[@]}"