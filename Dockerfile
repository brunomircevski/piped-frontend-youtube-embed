# syntax=docker/dockerfile:1
#
# Drop-in replacement for the official Piped frontend image (1337kavin/piped-frontend).
# The frontend source lives in frontend/ (upstream TeamPiped/Piped vendored as a git
# subtree, plus our changes). Same build, same nginx, same entrypoint/env vars.
#
# Build:  docker build -t piped-frontend-youtube-embed .
# Run:    docker run -e BACKEND_HOSTNAME=pipedapi.example.com -p 8080:80 piped-frontend-youtube-embed

FROM node:lts-alpine AS build

WORKDIR /app/

RUN --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache curl

COPY frontend/ .

RUN corepack enable && corepack prepare pnpm@latest --activate

RUN --mount=type=cache,target=/root/.local/share/pnpm \
    --mount=type=cache,target=/app/node_modules \
    pnpm install --frozen-lockfile --prefer-offline && \
    pnpm build && ./localizefonts.sh

FROM nginxinc/nginx-unprivileged:alpine

COPY --chown=101:101 --from=build /app/dist/ /usr/share/nginx/html/

COPY --chown=101:101 frontend/docker/nginx.conf /etc/nginx/conf.d/default.conf

COPY frontend/docker/entrypoint.sh /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
