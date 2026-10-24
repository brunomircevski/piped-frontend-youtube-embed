# Piped Frontend — YouTube Embed

A fork of the [Piped](https://github.com/TeamPiped/Piped) frontend that plays
videos through a [`youtube-nocookie.com`](https://www.youtube-nocookie.com)
embed instead of Piped's native player, with a refreshed, lighter design.

Everything else (search, subscriptions, feed, playlists, comments, SponsorBlock
data, …) still comes from your Piped backend — only the frontend is forked.

## Features

- **YouTube nocookie embed player** (preference *Use YouTube nocookie embed*,
  on by default; turn it off to get Piped's native Shaka player back).
- **Background playback on mobile.** When the screen turns off or you switch
  apps, YouTube's embed pauses itself for non-Premium viewers; the page resumes
  it. Needs a browser that doesn't suspend background media itself — e.g.
  Brave on Android with *Settings → Media → Background video playback* on.
  Can be turned off in Preferences.
- **SponsorBlock** segments are skipped (or offered as a *Skip* button) using
  your existing SponsorBlock preferences, with an *Undo* notice.
- **Autoplay next video / playlists / loop** work with the embed, including
  with the screen off.
- **Keyboard shortcuts:** `Space`/`K` play/pause, `←`/`→` ±5 s, `J`/`L` ±10 s,
  `M` mute, `F` fullscreen, `Shift+,`/`Shift+.` speed, `0`–`9` jump to 0–90 %,
  `Home`/`End`.
- **Playback speed** buttons 1×–2× (the embed API's maximum); the last speed is
  remembered and follows changes made in YouTube's own menu.
- **Watch progress** is saved per video and resumed; it also feeds Piped's watch
  history progress bars when watch history is enabled.
- Embed respects your Piped language, autoplay and captions preferences.
- Commenter avatars fall back to an initial when the backend returns none
  (current Piped backends return no comment avatars at all).

## Usage

It is a drop-in replacement for the standard Piped frontend image. Replace
`1337kavin/piped-frontend` with `bruno704/piped-frontend-youtube-embed`; the
same environment variables (`BACKEND_HOSTNAME`, `HTTP_MODE`, `HTTP_WORKERS`,
`HTTP_PORT`) apply.

## Try it locally

A self-contained stack is included for local testing:

```bash
docker compose -f docker-compose.test.yml up --build
```

Then open <http://piped.localhost:8080>.

For development, build and maintenance details, see [MAINTAINING.md](MAINTAINING.md).
