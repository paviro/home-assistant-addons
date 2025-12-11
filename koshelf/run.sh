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
if [ -z "$HEATMAP_SCALE_MAX" ] || [ "$HEATMAP_SCALE_MAX" == "" ]; then
    HEATMAP_SCALE_MAX="auto"
fi
DAY_START_TIME=$(bashio::config 'day_start_time')
TIMEZONE=$(bashio::config 'timezone')
TITLE=$(bashio::config 'title')
MIN_PAGES_PER_DAY=$(bashio::config 'min_pages_per_day')
MIN_TIME_PER_DAY=$(bashio::config 'min_time_per_day')
LANGUAGE=$(bashio::config 'language')

echo "Books path: $BOOKS_PATH"
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
if [[ -z "$BOOKS_PATH" || "$BOOKS_PATH" == "" ]] && [[ -z "$DATABASE_PATH" || "$DATABASE_PATH" == "" ]]; then
    echo ""
    echo "║"
    echo "║                                ⚠️  ERROR  ⚠️"
    echo "║"
    echo "║"
    echo "║  🚨 CONFIGURATION REQUIRED 🚨"
    echo "║"
    echo "║  At least ONE of the following must be configured:"
    echo "║"
    echo "║  📚 books_path     - Path to your EPUB files and KoReader metadata"
    echo "║  📊 database_path  - Path to KoReader's statistics.sqlite3 file"
    echo "║"
    echo "║  Example configurations:"
    echo "║"
    echo "║  Option 1 - Books only:"
    echo "║    books_path: /share/books"
    echo "║"
    echo "║  Option 2 - Statistics only:"
    echo "║    database_path: /share/koreader/statistics.sqlite3"
    echo "║"
    echo "║  Option 3 - Both (recommended):"
    echo "║    books_path: /share/books"
    echo "║    database_path: /share/koreader/statistics.sqlite3"
    echo "║"
    echo "║  💡 Remember: Files must be under /media/ or /share/ directories!"
    echo "║"
    echo "║"
    echo ""
    bashio::log.fatal "KoShelf addon configuration error - see detailed message above"
    bashio::exit.nok
fi

# Start building command with port
COMMAND="/usr/local/bin/koshelf --port 38492"

# Add books-path if provided
if [ -n "$BOOKS_PATH" ] && [ "$BOOKS_PATH" != "" ]; then
    COMMAND="$COMMAND --books-path \"$BOOKS_PATH\""
fi

# Add statistics-db if provided
if [ -n "$DATABASE_PATH" ] && [ "$DATABASE_PATH" != "" ]; then
    COMMAND="$COMMAND --statistics-db \"$DATABASE_PATH\""
fi

# Add optional --include-unread flag
if [ "$INCLUDE_UNREAD" = "true" ]; then
    COMMAND="$COMMAND --include-unread"
fi

# Add optional --include-all-stats flag
if [ "$INCLUDE_ALL_STATS" = "true" ]; then
    COMMAND="$COMMAND --include-all-stats"
fi

# Always include --heatmap-scale-max flag
COMMAND="$COMMAND --heatmap-scale-max \"$HEATMAP_SCALE_MAX\""

# Add optional day start time if provided
if [ -n "$DAY_START_TIME" ] && [ "$DAY_START_TIME" != "" ]; then
    COMMAND="$COMMAND --day-start-time \"$DAY_START_TIME\""
fi

# Add optional timezone if provided
if [ -n "$TIMEZONE" ] && [ "$TIMEZONE" != "" ]; then
    COMMAND="$COMMAND --timezone \"$TIMEZONE\""
fi

# Add optional docsettings-path if provided
if [ -n "$DOCSETTINGS_PATH" ] && [ "$DOCSETTINGS_PATH" != "" ]; then
    COMMAND="$COMMAND --docsettings-path \"$DOCSETTINGS_PATH\""
fi

# Add optional hashdocsettings-path if provided
if [ -n "$HASHDOCSETTINGS_PATH" ] && [ "$HASHDOCSETTINGS_PATH" != "" ]; then
    COMMAND="$COMMAND --hashdocsettings-path \"$HASHDOCSETTINGS_PATH\""
fi

# Add optional title if provided
if [ -n "$TITLE" ] && [ "$TITLE" != "" ]; then
    COMMAND="$COMMAND --title \"$TITLE\""
fi

# Add optional min-pages-per-day if provided
if [ -n "$MIN_PAGES_PER_DAY" ] && [ "$MIN_PAGES_PER_DAY" != "" ]; then
    COMMAND="$COMMAND --min-pages-per-day $MIN_PAGES_PER_DAY"
fi

# Add optional min-time-per-day if provided
if [ -n "$MIN_TIME_PER_DAY" ] && [ "$MIN_TIME_PER_DAY" != "" ]; then
    COMMAND="$COMMAND --min-time-per-day \"$MIN_TIME_PER_DAY\""
fi

# Add optional language if provided
if [ -n "$LANGUAGE" ] && [ "$LANGUAGE" != "" ]; then
    COMMAND="$COMMAND --language \"$LANGUAGE\""
fi

echo "Running: $COMMAND"

# Run koshelf
eval $COMMAND 