# syntax=docker/dockerfile:1
#
# Drop-in fork of the Piped frontend that can replace the Piped player with a
# youtube-nocookie.com embed. Built as a thin patch-overlay on top of upstream
# TeamPiped/Piped pinned at UPSTREAM_REF.
#
# Build:  docker build --build-arg UPSTREAM_REF=<sha> -t piped-frontend-youtube-embed .
# Run:    docker run -e BACKEND_HOSTNAME=pipedapi.example.com -p 8080:80 piped-frontend-youtube-embed

ARG UPSTREAM_REPO=https://github.com/TeamPiped/Piped.git
# Default ref; overridden at build time from the UPSTREAM_REF file (see scripts / README).
ARG UPSTREAM_REF=70453d1b5795d4acee90a33a2596a315ef72d961

#############################################
# Stage 1: fetch upstream + apply our changes
#############################################
FROM alpine/git AS source

ARG UPSTREAM_REPO
ARG UPSTREAM_REF

WORKDIR /src

# Clone upstream at the pinned ref. Use a shallow fetch of the exact commit.
RUN git init -q . && \
    git remote add origin "${UPSTREAM_REPO}" && \
    git fetch -q --depth 1 origin "${UPSTREAM_REF}" && \
    git checkout -q FETCH_HEAD

# Overlay: brand-new files we own (copied verbatim into the upstream tree).
COPY overlay/ /src/

# Patch: edits to existing upstream files. Must apply cleanly against UPSTREAM_REF.
COPY patches/ /patches/
RUN for p in /patches/*.patch; do \
        echo "Applying $p"; \
        git apply --whitespace=nowarn "$p"; \
    done

#############################################
# Stage 2: build the frontend (mirrors upstream Dockerfile)
#############################################
FROM node:lts-alpine AS build

WORKDIR /app/

RUN --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache curl

COPY --from=source /src/ /app/

RUN corepack enable && corepack prepare pnpm@latest --activate

RUN --mount=type=cache,target=/root/.local/share/pnpm \
    --mount=type=cache,target=/app/node_modules \
    pnpm install --prefer-offline && \
    pnpm build && ./localizefonts.sh

#############################################
# Stage 3: serve (mirrors upstream Dockerfile)
#############################################
FROM nginxinc/nginx-unprivileged:alpine

COPY --chown=101:101 --from=build /app/dist/ /usr/share/nginx/html/

COPY --chown=101:101 --from=source /src/docker/nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=source /src/docker/entrypoint.sh /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
