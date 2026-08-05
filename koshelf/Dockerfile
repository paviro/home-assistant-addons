ARG BUILD_FROM
FROM $BUILD_FROM

# Install required packages (bashio is already included in the HA base image)
RUN apk add --no-cache \
    curl \
    unzip

# Set the version
ARG KOSHELF_VERSION=2026.8.0

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
    i386|i686) RELEASE_ARCH="linux-${LIBC}-i686" ;; \
    armv7l|armhf) RELEASE_ARCH="linux-${LIBC}-armv7" ;; \
    *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
    esac && \
    echo "Detected: Architecture=${ARCH}, Libc=${LIBC}" && \
    echo "Downloading koshelf v${KOSHELF_VERSION} for ${RELEASE_ARCH}" && \
    curl -L -o /tmp/koshelf.zip \
    "https://github.com/paviro/KoShelf/releases/download/${KOSHELF_VERSION}/${RELEASE_ARCH}.zip" && \
    curl -L -o /tmp/SHA256SUMS \
    "https://github.com/paviro/KoShelf/releases/download/${KOSHELF_VERSION}/SHA256SUMS" && \
    grep " ${RELEASE_ARCH}.zip$" /tmp/SHA256SUMS | sed "s| ${RELEASE_ARCH}.zip| /tmp/koshelf.zip|" | sha256sum -c - && \
    unzip /tmp/koshelf.zip -d /tmp/ && \
    mv /tmp/koshelf /usr/local/bin/koshelf && \
    chmod +x /usr/local/bin/koshelf && \
    rm -rf /tmp/koshelf.zip /tmp/SHA256SUMS

# Copy the run script
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ] 
