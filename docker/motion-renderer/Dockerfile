# Linux/arm64 qualification image. Build context is the verified acquisition bundle,
# not the repository: no credentials, customer data or private evaluations are copied.
FROM node@sha256:af01d58b748ec92b1d6e8e11429aad424fd1e68c848185399dca0596a1ab8f5c
COPY dependencies/deb-sha256.txt /opt/deb-sha256.txt
RUN --network=none --mount=type=bind,source=dependencies/debs,target=/debs,ro \
    sha256sum --check /opt/deb-sha256.txt && \
    dpkg --install /debs/*.deb && \
    rm -rf /var/lib/apt/lists/*
COPY dependencies/playwright/ /opt/playwright/
COPY dependencies/browser/ /opt/browser/
COPY dependencies/manifest.json /opt/renderer-dependencies.json
COPY renderer/ /opt/renderer/
RUN --network=none chmod 0755 /opt/browser/chrome-headless-shell && \
    /usr/local/bin/node --version && /usr/bin/ffmpeg -version && /usr/bin/ffprobe -version
ENV PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/home TMPDIR=/tmp LANG=C.UTF-8
WORKDIR /opt/renderer
USER 65532:65532
ENTRYPOINT ["/usr/local/bin/node", "/opt/renderer/runner.cjs"]
