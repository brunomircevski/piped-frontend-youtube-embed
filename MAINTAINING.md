# Maintaining the Piped YouTube Embed fork

This document explains the architecture and the day-to-day workflows for
running, building, updating, and publishing the fork. It is written for both
humans and AI agents.

## Mental model

We do **not** vendor a copy of Piped. We keep only our own additions and a small
patch, and reconstruct the full source at build time:

```
piped-frontend-youtube-embed/
├── UPSTREAM_REF                 # pinned upstream commit SHA
├── Dockerfile                   # clone upstream @ ref -> overlay -> patch -> build
├── overlay/                     # NEW files we own (copied verbatim into upstream)
│   └── src/components/YouTubeEmbed.vue
├── patches/
│   └── piped-youtube-embed.patch   # diff to EXISTING upstream files
├── scripts/
│   ├── prepare.sh               # build a local .work/ tree (clone+overlay+patch)
│   ├── regen-patch.sh           # regenerate the patch from .work/
│   └── update-upstream.sh       # bump UPSTREAM_REF and re-verify
├── config/                      # nginx + backend config for local testing
└── docker-compose.test.yml      # local HTTP-only stack
```

Rule of thumb:

- A **brand-new file** -> put it in `overlay/` (mirrors the upstream path).
- A **change to an existing upstream file** -> edit it in `.work/` and
  regenerate the patch. Keep these changes as small as possible.

## What the fork changes

New file (overlay):

- `overlay/src/components/YouTubeEmbed.vue` — the nocookie iframe player with
  speed buttons and watch-progress save/resume. All the heavy logic lives here
  so the patch stays tiny.

Patched existing files (`patches/piped-youtube-embed.patch`):

- `src/components/PreferencesPage.vue` — adds the `youtubeNoCookieEmbed`
  preference (a `usePreferenceBoolean`) and renders it as the first item.
- `src/components/WatchVideo.vue` — conditionally renders `YouTubeEmbed` instead
  of `VideoPlayer`, and guards the `videoPlayer.value.loadVideo()` calls so the
  Shaka player is never initialised when embedding.
- `src/locales/en.json` — the `actions.youtube_nocookie_embed` label (other
  locales fall back to English automatically).

## Run locally (dev server, fast iteration)

```bash
./scripts/prepare.sh          # clones upstream @ UPSTREAM_REF into .work/, applies overlay+patch
cd .work
pnpm install
pnpm dev                      # Vite dev server
```

Point the dev server at any public Piped API by editing `.work/.env`
(`VITE_PIPED_API`) or via the in-app instance selector.

## Run locally (full Docker stack)

```bash
docker compose -f docker-compose.test.yml up --build
```

See [README.md](README.md#local-testing-http-only-no-https) for URLs and the
test checklist.

## Editing the fork

### Changing the new component

Edit `overlay/src/components/YouTubeEmbed.vue` directly. Re-run
`./scripts/prepare.sh` (or copy the file into `.work/`) and `pnpm dev` to test.
No patch regeneration needed — overlay files are copied verbatim.

### Changing an existing upstream file

1. Make sure `.work/` exists and is clean: `./scripts/prepare.sh`.
2. Edit the file(s) **inside `.work/`**.
3. Regenerate the patch:

   ```bash
   ./scripts/regen-patch.sh
   ```

   This writes `patches/piped-youtube-embed.patch` from `git diff` of `.work/`,
   automatically excluding any files we ship via `overlay/`.

4. Verify a clean re-apply from scratch:

   ```bash
   ./scripts/prepare.sh
   ```

## Updating to a newer upstream Piped

```bash
./scripts/update-upstream.sh
```

This resolves the latest upstream `master`, writes it to `UPSTREAM_REF`, and
re-runs `prepare.sh` to confirm the patch still applies.

- **Clean apply** -> done. Test (`cd .work && pnpm install && pnpm dev`),
  rebuild the image, optionally update the default `UPSTREAM_REF` ARG in the
  `Dockerfile`, commit, and re-publish.
- **Conflict** -> the patch no longer matches upstream. Resolve manually:
  1. Inspect which hunk failed (the script prints the error).
  2. Re-clone cleanly, copy overlay, then re-apply your intended edits to the
     existing files by hand inside `.work/`.
  3. `./scripts/regen-patch.sh` to capture the new patch.
  4. `./scripts/prepare.sh` to confirm a clean apply, then test.

Pinning to a commit (rather than tracking `master` blindly) means updates are
always deliberate and reproducible.

## Building the image

```bash
# Single-arch (local arch)
docker build -t piped-frontend-youtube-embed:latest .

# Multi-arch
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t piped-frontend-youtube-embed:latest \
  -t piped-frontend-youtube-embed:$(tr -d '[:space:]' < UPSTREAM_REF | cut -c1-12) \
  .
```

Suggested tagging: `latest` plus a tag derived from the short upstream SHA so
each image is traceable to the exact upstream commit it was built from.

## Release checklist

1. `./scripts/update-upstream.sh` (if updating upstream) — patch applies clean.
2. `docker compose -f docker-compose.test.yml up --build` — smoke test the
   feature on and off.
3. Build the image.
4. Commit `UPSTREAM_REF` + `patches/` changes.
