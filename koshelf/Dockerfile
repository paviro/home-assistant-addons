ARG BUILD_FROM
FROM $BUILD_FROM

# Install required packages
RUN apk add --no-cache \
    bash \
    curl \
    unzip

# Set the version
ARG KOSHELF_VERSION=1.0.17

# Detect architecture and libc, then download appropriate binary
RUN ARCH=$(uname -m) && \
    # Detect libc type (musl for Alpine, gnu for Debian/Ubuntu)
    if [ -f /etc/alpine-release ]; then \
        LIBC="musl"; \
    elif [ -f /lib/x86_64-linux-gnu/libc.so.6 ] || [ -f /lib/aarch64-linux-gnu/libc.so.6 ] || ldd --version 2>&1 | grep -q "GNU libc"; then \
        LIBC="gnu"; \
    else \
        echo "Cannot detect libc, defaulting to musl"; \
        LIBC="musl"; \
    fi && \
    case $ARCH in \
        x86_64) RELEASE_ARCH="linux-${LIBC}-x86_64" ;; \
        aarch64) RELEASE_ARCH="linux-${LIBC}-aarch64" ;; \
        i386|i686) RELEASE_ARCH="linux-${LIBC}-x86_64" ;; \
        armv7l|armhf) RELEASE_ARCH="linux-${LIBC}-aarch64" ;; \
        *) echo "Unsupported architecture: $ARCH, falling back to x86_64" && RELEASE_ARCH="linux-${LIBC}-x86_64" ;; \
    esac && \
    echo "Detected: Architecture=${ARCH}, Libc=${LIBC}" && \
    echo "Downloading koshelf v${KOSHELF_VERSION} for ${RELEASE_ARCH}" && \
    curl -L -o /tmp/koshelf.zip \
        "https://github.com/paviro/KoShelf/releases/download/v${KOSHELF_VERSION}/${RELEASE_ARCH}.zip" && \
    unzip /tmp/koshelf.zip -d /tmp/ && \
    mv /tmp/koshelf /usr/local/bin/koshelf && \
    chmod +x /usr/local/bin/koshelf && \
    rm -rf /tmp/koshelf.zip

# Copy the run script
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ] 