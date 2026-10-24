<template>
    <div class="relative size-full overflow-hidden bg-black">
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
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { getPreferenceBoolean, getPreferenceString } from "@/composables/usePreferences.js";
import { EMBED_MAX_RATE, EMBED_SPEEDS } from "@/composables/usePlayer.js";
import {
    MIN_RATE,
    MAX_RATE,
    readStoredSpeed,
    writeStoredSpeed,
    getStartSeconds,
    saveWatchProgress,
    categoryLabel,
} from "@/composables/usePlayback.js";

const emit = defineEmits(["timeupdate", "ended", "ratechange", "playingchange"]);

const IFRAME_ALLOW =
    "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen; web-share";

// After setPlaybackRate the player keeps reporting the old rate for a moment.
const RATE_SETTLE_MS = 2000;
const PROGRESS_SAVE_MS = 5000;
const SEEK_SMALL = 5;
const SEEK_LARGE = 10;

// YT.PlayerState
const ENDED = 0;
const PLAYING = 1;
const BUFFERING = 3;

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
    // null: follow the "autoplay video" preference
    autoplay: {
        type: Boolean,
        default: null,
    },
    // Handle keyboard shortcuts (off while minimized, so pages keep their keys)
    keyboard: {
        type: Boolean,
        default: true,
    },
});

const iframeEl = ref(null);
const currentRate = ref(readStoredSpeed());
const manualSegment = ref(null);
const skippedNotice = ref(null);

let currentTime = 0;
let duration = 0;
let playerState = -1;
let isMuted = false;
let rateApplied = false;
let pendingRate = null;
let pendingRateAt = 0;
let lastSave = 0;
let skippedNoticeTimer = null;
let readyTimers = [];

// Resolved once, so a re-render never reloads the iframe.
const initialStart = getStartSeconds(props.videoId, props.startTime);

function buildEmbedSrc(videoId, startSeconds) {
    const params = new URLSearchParams({
        autoplay: (props.autoplay ?? getPreferenceBoolean("playerAutoPlay", true)) ? "1" : "0",
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

function flushProgress() {
    if (duration > 0) saveWatchProgress(props.videoId, currentTime, duration);
}

// ---- Controls -------------------------------------------------------------

function storeSpeed(rate) {
    writeStoredSpeed(rate);
    currentRate.value = rate;
    emit("ratechange", rate);
}

function applyRate(rate) {
    rate = Math.min(rate, EMBED_MAX_RATE);
    pendingRate = rate;
    pendingRateAt = Date.now();
    postCommand("setPlaybackRate", [rate]);
}

function setPlaybackSpeed(rate) {
    storeSpeed(rate);
    applyRate(rate);
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

function pause() {
    postCommand("pauseVideo");
}

function togglePlayPause() {
    if (playerState === PLAYING || playerState === BUFFERING) pause();
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
    const current = Math.min(currentRate.value, EMBED_MAX_RATE);
    const next =
        direction > 0 ? EMBED_SPEEDS.find(rate => rate > current) : EMBED_SPEEDS.findLast(rate => rate < current);
    if (next !== undefined) setPlaybackSpeed(next);
}

function isFullScreenEnabled() {
    return Boolean(document.fullscreenElement);
}

// ---- SponsorBlock ---------------------------------------------------------

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

    if (state === PLAYING && !rateApplied) {
        // The last used speed carries over to every new video.
        rateApplied = true;
        if (currentRate.value !== 1) applyRate(currentRate.value);
    }
    emit("playingchange", state === PLAYING || state === BUFFERING);

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
    if (typeof info.playbackRate === "number" && rateApplied) onRateInfo(info.playbackRate);
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

function onRateInfo(rate) {
    if (pendingRate !== null) {
        if (rate !== pendingRate && Date.now() - pendingRateAt < RATE_SETTLE_MS) return;
        pendingRate = null;
    }
    // A faster speed saved in audio mode plays at the embed's maximum but stays saved.
    if (rate === EMBED_MAX_RATE && currentRate.value > EMBED_MAX_RATE) return;
    // Remember speed changes made from YouTube's own settings menu too.
    if (rate !== currentRate.value && rate >= MIN_RATE && rate <= MAX_RATE) storeSpeed(rate);
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
    // A video opened while the page is hidden (autoplay-next) may not start by itself.
    if (document.hidden && getPreferenceBoolean("playerAutoPlay", true)) play();
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
    if (document.hidden) flushProgress();
}

watch(
    () => props.keyboard,
    enabled => {
        if (enabled) document.addEventListener("keydown", onKeyDown);
        else document.removeEventListener("keydown", onKeyDown);
    },
    { immediate: true },
);

onMounted(() => {
    window.addEventListener("message", onMessage);
    document.addEventListener("visibilitychange", onVisibilityChange);
    window.addEventListener("pagehide", flushProgress);
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
    pause,
    togglePlayPause,
    setPlaybackSpeed,
    currentRate,
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
