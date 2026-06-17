# Piped Frontend — YouTube Embed

A fork of the [Piped](https://github.com/TeamPiped/Piped) frontend that plays
videos through a [`youtube-nocookie.com`](https://www.youtube-nocookie.com)
embed instead of Piped's native player.

The behaviour is controlled by a single preference, **Use YouTube nocookie
embed**, shown first on the Preferences page. It is **on by default**; turn it
off to use Piped's native (Shaka) player.

## Features

- Plays videos in a YouTube nocookie embed.
- Playback-speed buttons (x1, 1.25, 1.5, 1.75, 2, 2.5, 3); your last speed is
  remembered.
- Watch progress is saved per video and resumed when you return.

## Usage

It is a drop-in replacement for the standard Piped frontend image and is
configured the same way (via the `BACKEND_HOSTNAME` and `HTTP_MODE` environment
variables). Replace the frontend image in your Piped deployment with this one;
no other services change.

## Try it locally

A self-contained stack is included for local testing:

```bash
docker compose -f docker-compose.test.yml up --build
```

Then open <http://piped.localhost:8080>.

For build and maintenance details, see [MAINTAINING.md](MAINTAINING.md).
