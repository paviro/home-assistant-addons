#!/usr/bin/with-contenv bashio

echo "Starting koshelf addon..."

# Get configuration from addon
BOOKS_PATH=$(bashio::config 'books_path')
INCLUDE_UNREAD=$(bashio::config 'include_unread')
DATABASE_PATH=$(bashio::config 'database_path')
HEATMAP_SCALE_MAX=$(bashio::config 'heatmap_scale_max')
if [ -z "$HEATMAP_SCALE_MAX" ] || [ "$HEATMAP_SCALE_MAX" == "" ]; then
    HEATMAP_SCALE_MAX="auto"
fi
DAY_START_TIME=$(bashio::config 'day_start_time')
TIMEZONE=$(bashio::config 'timezone')

echo "Books path: $BOOKS_PATH"
echo "Include unread: $INCLUDE_UNREAD"
echo "Database path: $DATABASE_PATH"
echo "Heatmap scale max: $HEATMAP_SCALE_MAX"
echo "Day start time: $DAY_START_TIME"
echo "Timezone: $TIMEZONE"

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

echo "Running: $COMMAND"

# Run koshelf
eval $COMMAND 