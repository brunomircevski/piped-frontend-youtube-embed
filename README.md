# Piped Frontend — YouTube Embed

A fork of the [Piped](https://github.com/TeamPiped/Piped) frontend that plays
videos through a [`youtube-nocookie.com`](https://www.youtube-nocookie.com)
embed instead of Piped's native player, with a refreshed, lighter design.

Everything else (search, subscriptions, feed, playlists, comments, SponsorBlock
data, …) still comes from your Piped backend — only the frontend is forked.

## Features

- **YouTube nocookie embed player** (preference *Use YouTube nocookie embed*,
  on by default; turn it off to get Piped's native Shaka player back).
- **Mini player.** Leave a video (swipe it down on phones, or *Miniplayer* on
  desktop) and it keeps playing in a small player while you browse channels,
  subscriptions, search, … Tap it to go back; it continues with the next
  playlist/related video according to your autoplay setting.
- **YouTube-app-like phone layout:** the video stays pinned at the top, the
  header and bottom navigation step aside, comments open in a sheet above the
  recommendations, and a bottom navigation bar is shown everywhere else.
- **Audio mode** (*Audio* button on the watch page): hides the embed and plays
  just the sound from your Piped proxy, so it **keeps playing with the screen
  off or in the background** (Brave on Android: *Background video playback*
  on). Lock-screen controls, SponsorBlock, loop and autoplay-next work in it;
  *Video* switches back to the embed at the same second. The *Audio only*
  preference opens videos in audio mode.
- **Automatic audio when the screen turns off** (phones, on by default): when
  the page is hidden while a video plays, it switches to the (preloaded) audio
  player, and back to the video at the new position when you return. Can be
  turned off in Preferences.
- **Landscape = fullscreen** on phones: turning the phone sideways on the watch
  page fills the screen with the video.
- **Open in YouTube** button that opens the video at the current time on
  youtube.com.
- **SponsorBlock** segments are skipped (or offered as a *Skip* button) using
  your existing SponsorBlock preferences, with an *Undo* notice.
- **Autoplay next video / playlists / loop** work with the embed, including
  with the screen off.
- **Keyboard shortcuts:** `Space`/`K` play/pause, `←`/`→` ±5 s, `J`/`L` ±10 s,
  `M` mute, `F` fullscreen, `Shift+,`/`Shift+.` speed, `0`–`9` jump to 0–90 %,
  `Home`/`End`.
- **Playback speed** buttons 1×–2× (the embed API's maximum). The last speed —
  including one picked in YouTube's own settings menu — is remembered and
  applied to every new video.
- **Watch progress** is saved per video and resumed; it also feeds Piped's watch
  history progress bars when watch history is enabled.
- Embed respects your Piped language, autoplay and captions preferences.
- Commenter avatars fall back to an initial when the backend returns none
  (current Piped backends return no comment avatars at all).

## Limitations

- **The embed itself stops when the screen is off on phones.** YouTube's embed
  player suspends playback when the page is hidden on mobile unless the viewer
  has YouTube Premium, and Brave's workaround only applies to youtube.com. Use
  audio mode for screen-off listening.
- **Audio mode needs the backend's streams.** It plays the audio-only stream if
  the backend returns one, otherwise the muxed 360p stream (itag 18, ~96 kbps
  AAC). If your Piped backend can't extract streams for a video, audio mode
  shows a message and the embed still works.

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
