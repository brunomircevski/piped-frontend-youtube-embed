<template>
    <div class="block w-full max-w-full">
        <div
            class="relative overflow-hidden bg-black"
            :class="isEmbed ? 'size-full' : 'aspect-video max-h-[75vh] w-full sm:rounded-xl'"
        >
            <iframe
                ref="iframeEl"
                class="block size-full border-0"
                :src="iframeSrc"
                title="YouTube video player"
                :allow="IFRAME_ALLOW"
                referrerpolicy="strict-origin-when-cross-origin"
                allowfullscreen
                @load="onIframeLoad"
            />

            <!-- SponsorBlock: manual skip / "skipped" notice -->
            <Transition name="fade">
                <button
                    v-if="manualSegment"
                    type="button"
                    class="absolute right-3 bottom-16 flex items-center gap-2 rounded-full bg-black/75 px-4 py-2 text-sm font-medium text-white ring-1 ring-white/30 backdrop-blur-sm hover:bg-black/90"
                    @click="skipSegment(manualSegment)"
                >
                    {{ $t("actions.skip_segment") }}
                    <span class="opacity-70">· {{ categoryLabel(manualSegment.category) }}</span>
                    <i-fa6-solid-forward-step />
                </button>
                <div
                    v-else-if="skippedNotice"
                    class="absolute right-3 bottom-16 flex items-center gap-3 rounded-full bg-black/75 py-1.5 pr-1.5 pl-4 text-sm text-white ring-1 ring-white/20 backdrop-blur-sm"
                >
                    <span>{{ $t("info.skipped") }} {{ categoryLabel(skippedNotice.category).toLowerCase() }}</span>
                    <button
                        v-t="'player.undo'"
                        type="button"
                        class="rounded-full bg-white/15 px-3 py-1 font-medium hover:bg-white/25"
                        @click="undoSkip"
                    />
                </div>
            </Transition>
        </div>

        <div v-if="!isEmbed" class="mt-2 flex flex-wrap items-center justify-end gap-2 max-sm:px-3">
            <span v-t="'actions.playback_speed'" class="text-sm text-muted max-sm:hidden" />
            <div class="segmented" role="group" :aria-label="$t('actions.playback_speed')">
                <button
                    v-for="rate in speeds"
                    :key="rate"
                    type="button"
                    :aria-pressed="currentRate === rate"
                    @click="setPlaybackSpeed(rate)"
                    v-text="`${rate}×`"
                />
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, onActivated, onDeactivated } from "vue";
import { getPreferenceBoolean, getPreferenceString } from "@/composables/usePreferences.js";

const emit = defineEmits(["timeupdate", "ended"]);

const IFRAME_ALLOW =
    "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen; web-share";

const STORAGE_SPEED_KEY = "playbackRate";
const STORAGE_PROGRESS_KEY = "watchProgress";
// The embed API clamps anything above 2x, so faster buttons would be lies.
const SPEEDS = [1, 1.25, 1.5, 1.75, 2];
const MIN_SAVE_SECONDS = 10;
const MAX_PROGRESS_RATIO = 0.9;
const MAX_PROGRESS_ENTRIES = 500;
const PROGRESS_SAVE_MS = 5000;
const SEEK_SMALL = 5;
const SEEK_LARGE = 10;
// How long after the page is hidden a pause is treated as YouTube's own
// "not backgroundable" pause rather than the user pressing pause.
const BACKGROUND_RESUME_WINDOW_MS = 6000;
const MAX_BACKGROUND_RESUMES = 5;

// YT.PlayerState
const ENDED = 0;
const PLAYING = 1;
const PAUSED = 2;
const BUFFERING = 3;

const CATEGORY_LABELS = {
    sponsor: "Sponsor",
    selfpromo: "Self-promotion",
    interaction: "Interaction reminder",
    intro: "Intro",
    outro: "Outro",
    preview: "Preview",
    music_offtopic: "Non-music section",
    filler: "Filler",
};

const props = defineProps({
    videoId: {
        type: String,
        required: true,
    },
    // Explicit start time from the URL (?t=). When > 0 it overrides saved progress.
    startTime: {
        type: Number,
        default: 0,
    },
    sponsors: {
        type: Object,
        default: null,
    },
    loop: Boolean,
    isEmbed: Boolean,
});

const iframeEl = ref(null);
const speeds = SPEEDS;
const currentRate = ref(readStoredSpeed());
const manualSegment = ref(null);
const skippedNotice = ref(null);

let currentTime = 0;
let duration = 0;
let playerState = -1;
let isMuted = false;
let rateApplied = false;
let lastSave = 0;
let hiddenAt = 0;
let playingWhenHidden = false;
let backgroundResumes = 0;
let skippedNoticeTimer = null;
let readyTimers = [];

// Resolved once, so a re-render never reloads the iframe.
const initialStart = getStartSeconds(props.videoId);

function readJSON(key) {
    try {
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

function writeJSON(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch {
        /* ignore quota / disabled storage */
    }
}

function readStoredSpeed() {
    try {
        const n = Number(localStorage.getItem(STORAGE_SPEED_KEY) ?? 1);
        return SPEEDS.includes(n) ? n : 1;
    } catch {
        return 1;
    }
}

function isRestorableProgress(time, total) {
    return total > 0 && time >= MIN_SAVE_SECONDS && time < total * MAX_PROGRESS_RATIO;
}

function getStartSeconds(videoId) {
    if (props.startTime > 0) return Math.floor(props.startTime);
    const entry = (readJSON(STORAGE_PROGRESS_KEY) || {})[videoId];
    if (entry && isRestorableProgress(entry.currentTime, entry.duration)) return Math.floor(entry.currentTime);
    return 0;
}

function buildEmbedSrc(videoId, startSeconds) {
    const params = new URLSearchParams({
        autoplay: getPreferenceBoolean("playerAutoPlay", true) ? "1" : "0",
        enablejsapi: "1",
        origin: location.origin,
        widget_referrer: location.origin,
        playsinline: "1",
        rel: "0",
        iv_load_policy: "3",
    });
    const hl = getPreferenceString("hl", "en");
    if (hl) params.set("hl", hl.replace("_", "-"));
    if (getPreferenceBoolean("autoDisplayCaptions", false)) params.set("cc_load_policy", "1");
    if (startSeconds > 0) params.set("start", String(startSeconds));
    return `https://www.youtube-nocookie.com/embed/${videoId}?${params}`;
}

const iframeSrc = computed(() => buildEmbedSrc(props.videoId, initialStart));

function postToPlayer(message) {
    iframeEl.value?.contentWindow?.postMessage(JSON.stringify(message), "*");
}

function postCommand(func, args = []) {
    postToPlayer({ event: "command", func, args, id: 1, channel: "widget" });
}

function startListening() {
    postToPlayer({ event: "listening", id: 1, channel: "widget" });
    postCommand("addEventListener", ["onStateChange"]);
}

// ---- Watch progress -------------------------------------------------------

function saveWatchProgress(videoId, time, total) {
    if (!videoId || !(total > 0)) return;
    const all = readJSON(STORAGE_PROGRESS_KEY) || {};

    if (isRestorableProgress(time, total)) {
        all[videoId] = { currentTime: Math.floor(time), duration: Math.floor(total), updatedAt: Date.now() };
        const ids = Object.keys(all);
        if (ids.length > MAX_PROGRESS_ENTRIES) {
            ids.sort((a, b) => (all[a].updatedAt ?? 0) - (all[b].updatedAt ?? 0));
            ids.slice(0, ids.length - MAX_PROGRESS_ENTRIES).forEach(id => delete all[id]);
        }
    } else {
        delete all[videoId];
    }
    writeJSON(STORAGE_PROGRESS_KEY, all);
    updateHistoryDatabase(videoId, time);
}

// Keeps Piped's watch history (thumbnail progress bars) in sync, like the native player.
function updateHistoryDatabase(videoId, time) {
    if (!window.db) return;
    try {
        const store = window.db.transaction("watch_history", "readwrite").objectStore("watch_history");
        const request = store.get(videoId);
        request.onsuccess = event => {
            const entry = event.target.result;
            if (!entry) return;
            entry.currentTime = time;
            store.put(entry);
        };
    } catch {
        /* history disabled or db unavailable */
    }
}

function flushProgress() {
    if (duration > 0) saveWatchProgress(props.videoId, currentTime, duration);
}

// ---- Controls -------------------------------------------------------------

function setPlaybackSpeed(rate) {
    try {
        localStorage.setItem(STORAGE_SPEED_KEY, String(rate));
    } catch {
        /* ignore */
    }
    currentRate.value = rate;
    postCommand("setPlaybackRate", [rate]);
}

function seek(time, exact = false) {
    const target = Math.max(0, exact ? time : Math.floor(time));
    postCommand("seekTo", [target, true]);
    currentTime = target;
    emit("timeupdate", target);
}

function seekRelative(delta) {
    seek(Math.min(currentTime + delta, duration > 0 ? duration : Infinity), true);
}

function play() {
    postCommand("playVideo");
}

function togglePlayPause() {
    if (playerState === PLAYING || playerState === BUFFERING) postCommand("pauseVideo");
    else play();
}

function toggleMute() {
    isMuted = !isMuted;
    postCommand(isMuted ? "mute" : "unMute");
}

function toggleFullscreen() {
    if (document.fullscreenElement) document.exitFullscreen();
    else iframeEl.value?.requestFullscreen?.();
}

function changeSpeed(direction) {
    const index = SPEEDS.indexOf(currentRate.value);
    const next = SPEEDS[Math.min(Math.max(index + direction, 0), SPEEDS.length - 1)];
    if (next !== undefined) setPlaybackSpeed(next);
}

function isFullScreenEnabled() {
    return Boolean(document.fullscreenElement);
}

// ---- SponsorBlock ---------------------------------------------------------

function categoryLabel(category) {
    return CATEGORY_LABELS[category] ?? category;
}

function findSegment(time) {
    return props.sponsors?.segments?.find(s => time >= s.segment[0] && time < s.segment[1] - 0.5);
}

function skipSegment(segment) {
    segment.skipped = true;
    manualSegment.value = null;
    seek(segment.segment[1], true);
    clearTimeout(skippedNoticeTimer);
    skippedNotice.value = segment;
    skippedNoticeTimer = setTimeout(() => (skippedNotice.value = null), 5000);
}

function undoSkip() {
    const segment = skippedNotice.value;
    skippedNotice.value = null;
    if (segment) seek(segment.segment[0], true);
}

function handleSegments(time) {
    const segment = findSegment(time);
    if (!segment) {
        manualSegment.value = null;
        return;
    }
    if (segment.autoskip && (!segment.skipped || props.loop)) skipSegment(segment);
    else if (!segment.autoskip) manualSegment.value = segment;
}

watch(
    () => props.sponsors,
    () => props.sponsors?.segments?.forEach(segment => (segment.skipped = false)),
);

// ---- Keyboard -------------------------------------------------------------

function shouldIgnoreKeyboard(event) {
    if (event.ctrlKey || event.metaKey || event.altKey) return true;
    const target = event.target;
    if (!(target instanceof HTMLElement)) return false;
    return ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) || target.isContentEditable;
}

function onKeyDown(event) {
    if (shouldIgnoreKeyboard(event)) return;

    const actions = {
        Space: togglePlayPause,
        KeyK: togglePlayPause,
        ArrowLeft: () => seekRelative(-SEEK_SMALL),
        ArrowRight: () => seekRelative(SEEK_SMALL),
        KeyJ: () => seekRelative(-SEEK_LARGE),
        KeyL: () => seekRelative(SEEK_LARGE),
        KeyM: toggleMute,
        KeyF: toggleFullscreen,
        Comma: () => event.shiftKey && changeSpeed(-1),
        Period: () => event.shiftKey && changeSpeed(1),
        Home: () => seek(0),
        End: () => duration > 0 && seek(duration - 1),
    };
    const digit = /^Digit(\d)$/.exec(event.code);
    if (digit && duration > 0) actions[event.code] = () => seek((duration * Number(digit[1])) / 10);

    const action = actions[event.code];
    if (!action) return;
    // Space scrolls the page and arrows move focus; only steal keys we handle.
    event.preventDefault();
    action();
}

// ---- Player events --------------------------------------------------------

function onStateChange(state) {
    const previous = playerState;
    playerState = state;

    if (state === PLAYING) {
        if (!rateApplied) {
            rateApplied = true;
            if (currentRate.value !== 1) postCommand("setPlaybackRate", [currentRate.value]);
        }
    }

    // Mobile YouTube pauses non-Premium playback when the page is hidden. If that
    // happens right after the screen turns off / the app is switched, resume it.
    if (
        state === PAUSED &&
        previous !== PAUSED &&
        document.hidden &&
        playingWhenHidden &&
        Date.now() - hiddenAt < BACKGROUND_RESUME_WINDOW_MS &&
        backgroundResumes < MAX_BACKGROUND_RESUMES &&
        getPreferenceBoolean("embedBackgroundPlayback", true)
    ) {
        backgroundResumes++;
        play();
    }

    if (state === ENDED && previous !== ENDED) {
        if (duration > 0) saveWatchProgress(props.videoId, duration, duration);
        if (props.loop) {
            props.sponsors?.segments?.forEach(segment => (segment.skipped = false));
            seek(0);
            play();
        } else emit("ended");
    }
}

function onInfo(info) {
    if (typeof info.duration === "number" && info.duration > 0) duration = info.duration;
    if (typeof info.muted === "boolean") isMuted = info.muted;
    if (typeof info.playbackRate === "number" && rateApplied && SPEEDS.includes(info.playbackRate)) {
        // Follow speed changes made from YouTube's own settings menu.
        currentRate.value = info.playbackRate;
    }
    if (typeof info.playerState === "number" && info.playerState !== playerState) onStateChange(info.playerState);

    if (typeof info.currentTime === "number") {
        currentTime = info.currentTime;
        emit("timeupdate", currentTime);
        handleSegments(currentTime);
        if (Date.now() - lastSave > PROGRESS_SAVE_MS && duration > 0 && playerState === PLAYING) {
            lastSave = Date.now();
            saveWatchProgress(props.videoId, currentTime, duration);
        }
    }
}

function onMessage(event) {
    if (!iframeEl.value || event.source !== iframeEl.value.contentWindow) return;
    let data;
    try {
        data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
    } catch {
        return;
    }

    switch (data?.event) {
        case "onReady":
            clearReadyTimers();
            onReady();
            break;
        case "initialDelivery":
        case "infoDelivery":
            if (data.info) onInfo(data.info);
            break;
        case "onStateChange":
            if (typeof data.info === "number" && data.info !== playerState) onStateChange(data.info);
            break;
    }
}

function onReady() {
    // A video opened while the page is hidden (autoplay-next with the screen off)
    // may not start by itself.
    if (document.hidden && getPreferenceBoolean("playerAutoPlay", true)) {
        playingWhenHidden = true;
        hiddenAt = Date.now();
        play();
    }
}

function clearReadyTimers() {
    readyTimers.forEach(clearTimeout);
    readyTimers = [];
}

function onIframeLoad() {
    // The player only starts talking once it receives "listening"; retry until it does.
    clearReadyTimers();
    startListening();
    readyTimers = [250, 750, 1500, 3000].map(delay => setTimeout(startListening, delay));
}

function onVisibilityChange() {
    if (document.hidden) {
        hiddenAt = Date.now();
        playingWhenHidden = playerState === PLAYING || playerState === BUFFERING;
        backgroundResumes = 0;
        flushProgress();
    } else {
        hiddenAt = 0;
        playingWhenHidden = false;
    }
}

onMounted(() => {
    // Also attached in onActivated; the browser ignores the duplicate.
    document.addEventListener("keydown", onKeyDown);
    window.addEventListener("message", onMessage);
    document.addEventListener("visibilitychange", onVisibilityChange);
    window.addEventListener("pagehide", flushProgress);
});

// Inside <keep-alive> a cached watch page must not react to keys.
onActivated(() => document.addEventListener("keydown", onKeyDown));
onDeactivated(() => {
    flushProgress();
    document.removeEventListener("keydown", onKeyDown);
});

onBeforeUnmount(() => {
    flushProgress();
    clearReadyTimers();
    clearTimeout(skippedNoticeTimer);
    window.removeEventListener("message", onMessage);
    document.removeEventListener("keydown", onKeyDown);
    document.removeEventListener("visibilitychange", onVisibilityChange);
    window.removeEventListener("pagehide", flushProgress);
});

defineExpose({
    seek,
    play,
    isFullScreenEnabled,
});
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>
