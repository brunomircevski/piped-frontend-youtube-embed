# Maintaining the Piped YouTube Embed fork

## Layout

```
piped-frontend-youtube-embed/
├── frontend/                 # upstream TeamPiped/Piped (git subtree) + our changes
├── Dockerfile                # builds frontend/ exactly like upstream's image
├── scripts/update-upstream.sh
├── config/                   # nginx + backend config for the local test stack
└── docker-compose.test.yml   # local HTTP-only stack (frontend + backend + proxy)
```

`frontend/` is a squashed `git subtree` of upstream. Our changes are ordinary
commits on top, so you edit files there directly. Upstream is mostly quiet these
days (translations), so conflicts should be rare.

## What the fork changes

- `src/components/YouTubeEmbed.vue` — the embed player (IFrame API over
  `postMessage`): speed, progress save/resume, SponsorBlock, background-playback
  resume, keyboard shortcuts, loop/ended handling.
- `src/components/WatchVideo.vue` — renders `YouTubeEmbed` instead of
  `VideoPlayer` when the `youtubeNoCookieEmbed` preference is on; redesigned
  watch page.
- `src/components/PreferencesPage.vue` — `youtubeNoCookieEmbed` and
  `embedBackgroundPlayback` preferences; redesigned.
- `src/app.css` — design tokens (CSS variables for light/dark) and the shared
  classes `btn`, `input`, `segmented`, `card`, `chip`, `link`, `video-grid`,
  `pref-row`, …, declared with `@utility` so the Tailwind ESLint plugin knows
  them. Prefer these over long ad-hoc class strings.
- `src/components/ui/Avatar.vue` — avatar with initial-letter fallback.
- Most other components: restyled to use the tokens/classes above.
- `src/locales/en.json` — new strings (other locales fall back to English).
- `package.json`/`pnpm-lock.yaml` — dependencies bumped within their major
  versions (security fixes in DOMPurify and Vue).

## Develop

```bash
cd frontend
pnpm install
VITE_PIPED_API=http://pipedapi.localhost:8080 pnpm dev   # or any public Piped API
```

ESLint (incl. Prettier) runs inside the Vite dev server; fix issues with
`pnpm lint` / `pnpm format` or `npx eslint --fix <files>`.

## Pull upstream changes

```bash
./scripts/update-upstream.sh
```

This runs `git subtree pull --squash` from upstream `master` into `frontend/`.
Resolve conflicts like any merge. If `pnpm-lock.yaml` conflicts, take either
side and re-run `pnpm install` in `frontend/` to regenerate it.

## Local test stack

```bash
docker compose -f docker-compose.test.yml up --build
```

Open <http://piped.localhost:8080>. If Docker builds fail with DNS errors
(`apk` can't reach `dl-cdn.alpinelinux.org`), build with host networking first:

```bash
docker build --network=host -t piped-frontend-youtube-embed:dev .
docker compose -f docker-compose.test.yml up -d --no-build
```

## Build and publish

```bash
docker build -t bruno704/piped-frontend-youtube-embed:latest .
docker push bruno704/piped-frontend-youtube-embed:latest
```

Multi-arch:

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t bruno704/piped-frontend-youtube-embed:latest --push .
```
