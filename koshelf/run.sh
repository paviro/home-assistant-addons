#!/usr/bin/with-contenv bashio

echo "Starting koshelf addon..."

# Get configuration from addon
BOOKS_PATH=$(bashio::config 'books_path')
INCLUDE_UNREAD=$(bashio::config 'include_unread')
DATABASE_PATH=$(bashio::config 'database_path')

echo "Books path: $BOOKS_PATH"
echo "Include unread: $INCLUDE_UNREAD"
echo "Database path: $DATABASE_PATH"

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

echo "Running: $COMMAND"

# Run koshelf
eval $COMMAND 