import { reactive, ref, shallowRef, markRaw } from "vue";
import { fetchJson, apiUrl } from "./useApi.js";
import { getPreferenceNumber } from "./usePreferences.js";
import { fetchSponsors } from "./useSponsors.js";

// The YouTube embed lives once at the app root (GlobalPlayer.vue), so playback
// survives navigation: while a watch page is open it is drawn over that page's
// placeholder ("full"); after leaving the page it shrinks into the mini player.
// Moving an iframe in the DOM reloads it, so it is only ever restyled, never moved.
function storedRate() {
    try {
        return Number(localStorage.getItem("playbackRate")) || 1;
    } catch {
        return 1;
    }
}

export const player = reactive({
    videoId: null,
    startTime: 0,
    watchUrl: null,
    title: "",
    uploader: "",
    thumbnail: "",
    sponsors: null,
    loop: false,
    // "full" | "mini"; irrelevant while videoId is null
    mode: "full",
    // Watch page currently showing this video: { onEnded }
    owner: null,
    // Placeholder element the full player covers
    slot: null,
    // Autoplay queue used while minimized: { id, items, index } and related videos
    playlist: null,
    related: [],
    currentTime: 0,
    playing: false,
    rate: storedRate(),
    // Vertical drag offset while swiping the full player down
    dragOffset: 0,
    // Audio-only player (AudioPlayer.vue) instead of the embed; kept across videos
    audioMode: false,
    // Bumped on every switch between embed and audio, to remount the embed
    playerEpoch: 0,
    // The watch page's /streams response, so the audio player can preload
    streams: null,
    // Whether the player being switched to should start playing (null: preference)
    resumePlaying: null,
});

// Speed buttons; the embed API clamps anything above 2x, so faster ones would be lies.
export const SPEEDS = [1, 1.25, 1.5, 1.75, 2, 2.5, 3];
// YouTube's embed caps playback speed at 2×; faster speeds only apply in audio mode.
export const EMBED_MAX_RATE = 2;
export const EMBED_SPEEDS = SPEEDS.filter(rate => rate <= EMBED_MAX_RATE);

// Exposed controls of the mounted YouTubeEmbed (seek, play, pause, ...)
export const embed = shallowRef(null);

const mobileQuery = window.matchMedia("(max-width: 1023.98px)");
export const isMobileLayout = ref(mobileQuery.matches);
mobileQuery.addEventListener("change", e => (isMobileLayout.value = e.matches));

export function openVideo({ videoId, startTime = 0, watchUrl, title, uploader, thumbnail }) {
    if (player.videoId !== videoId) {
        player.videoId = videoId;
        player.startTime = startTime;
        player.currentTime = startTime;
        player.sponsors = null;
        player.loop = false;
        player.playlist = null;
        player.related = [];
        player.owner = null;
        player.playing = false;
        player.resumePlaying = null;
        player.streams = null;
        player.title = "";
        player.uploader = "";
        player.thumbnail = "";
    }
    if (watchUrl) player.watchUrl = watchUrl;
    if (title) player.title = title;
    if (uploader) player.uploader = uploader;
    if (thumbnail) player.thumbnail = thumbnail;
}

export function attachPlayer(owner, slot) {
    player.owner = markRaw(owner);
    player.slot = slot ? markRaw(slot) : null;
    player.mode = "full";
    player.dragOffset = 0;
}

export function setPlayerSlot(owner, slot) {
    if (player.owner === owner) player.slot = slot ? markRaw(slot) : null;
}

// Called when the watch page goes away; playback continues in the mini player.
export function detachPlayer(owner) {
    if (player.owner !== owner) return;
    player.slot = null;
    player.mode = "mini";
    player.dragOffset = 0;
}

export function releasePlayer(owner) {
    if (player.owner === owner) player.owner = null;
}

export function closePlayer() {
    player.videoId = null;
    player.owner = null;
    player.slot = null;
    player.playing = false;
    player.mode = "full";
}

// Switches between the embed and the audio-only player at the current position.
export function setAudioMode(enabled) {
    if (player.audioMode === enabled) return;
    player.startTime = Math.floor(player.currentTime);
    player.resumePlaying = player.playing;
    player.audioMode = enabled;
    player.playerEpoch++;
}

// "Next" from the lock screen / notification.
export function skipToNext() {
    if (player.mode === "full" && player.owner?.next) player.owner.next();
    else playNextInMiniPlayer();
}

export function onPlayerEnded() {
    if (player.mode === "full") player.owner?.onEnded?.();
    else playNextInMiniPlayer();
}

function nextItem() {
    const autoplay = getPreferenceNumber("autoplay", 1);
    const playlist = player.playlist;
    // playlist.index is the 1-based position of the current video
    if (autoplay >= 1 && playlist && playlist.index < playlist.items.length) {
        const item = playlist.items[playlist.index];
        return {
            ...item,
            url: `${item.url}&list=${playlist.id}&index=${playlist.index + 1}`,
            playlist: { ...playlist, index: playlist.index + 1 },
        };
    }
    if (autoplay >= 2 && player.related.length > 0) return player.related[0];
    return null;
}

async function playNextInMiniPlayer() {
    const next = nextItem();
    if (!next) return;
    const videoId = new URL(next.url, location.origin).searchParams.get("v");
    if (!videoId) return;

    openVideo({
        videoId,
        watchUrl: next.url,
        title: next.title,
        uploader: next.uploaderName,
        thumbnail: next.thumbnail,
    });
    player.playlist = next.playlist ?? null;

    const [streams, sponsors] = await Promise.all([
        fetchJson(apiUrl() + "/streams/" + videoId).catch(() => null),
        fetchSponsors(videoId),
    ]);
    if (player.videoId !== videoId) return;
    player.related = streams?.relatedStreams ?? [];
    if (streams) player.streams = { ...streams, id: videoId };
    player.sponsors = sponsors;
}

// Leaves the watch page so the video continues in the mini player: back to the
// page the user came from, unless that is another video.
export function minimizePlayer(router) {
    const back = window.history.state?.back;
    if (back && !String(router.resolve(back).name ?? "").startsWith("WatchVideo")) router.back();
    else router.push("/");
}
