ARG BUILD_FROM=alpine:3.23
FROM ${BUILD_FROM}
RUN apk add --no-cache python3 nginx ca-certificates tzdata
ARG BUILD_ARCH
COPY upstream.json install.py /opt/koshelf-addon/
RUN python3 /opt/koshelf-addon/install.py "${BUILD_ARCH}"
COPY addon.py /opt/koshelf-addon/addon.py
COPY UPSTREAM-LICENSE UPSTREAM.md /usr/share/doc/koshelf/
COPY run.sh /run.sh
RUN chmod 755 /run.sh
HEALTHCHECK --interval=30s --timeout=12s --start-period=120s --retries=3 \
    CMD ["python3", "/opt/koshelf-addon/addon.py", "--healthcheck"]
ENTRYPOINT ["/run.sh"]
