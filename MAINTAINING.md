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
  `postMessage`): speed, progress save/resume, SponsorBlock, keyboard
  shortcuts, loop/ended handling.
- `src/composables/usePlayer.js` + `src/components/GlobalPlayer.vue` — one
  embed for the whole app, rendered in `App.vue`. A watch page registers a
  placeholder element and the player is positioned over it (pinned to the top
  on phones); when the page is left it becomes the mini player. The iframe is
  only restyled, never moved in the DOM (moving an iframe reloads it).
- `src/components/WatchVideo.vue` — uses the global player instead of
  `VideoPlayer` when the `youtubeNoCookieEmbed` preference is on (the `/embed/`
  route still renders its own `YouTubeEmbed`); redesigned watch page, comments
  sheet on phones.
- `src/components/AudioPlayer.vue` — audio mode: an `<audio>` element on our
  origin (so the browser keeps it playing with the screen off) fed from the
  backend's audio or muxed stream, with Media Session controls, SponsorBlock and
  the same keyboard shortcuts. GlobalPlayer swaps it for the embed
  (`setAudioMode` in `usePlayer.js`) at the current position.
- `src/composables/usePlayback.js` — remembered speed, watch progress and
  SponsorBlock labels shared by both players.
- `src/components/BottomNav.vue` — bottom navigation below the `lg` breakpoint.
- `src/composables/useSponsors.js` — SponsorBlock fetch shared by the watch page
  and the mini player's autoplay.
- `src/components/PreferencesPage.vue` — `youtubeNoCookieEmbed` preference;
  redesigned.
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

Images are pushed by hand to GitHub Container Registry as
`ghcr.io/brunomircevski/piped-frontend`. Log in once with a GitHub token that
has the `write:packages` scope, then build and push:

```bash
docker login ghcr.io -u brunomircevski
docker build --network=host -t ghcr.io/brunomircevski/piped-frontend:latest .
docker push ghcr.io/brunomircevski/piped-frontend:latest
```
