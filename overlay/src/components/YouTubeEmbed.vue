<template>
    <div class="block w-full max-w-full">
        <iframe
            ref="iframeEl"
            :class="
                isEmbed
                    ? 'block size-full border-0 bg-black'
                    : 'block aspect-video max-h-[75vh] min-h-64 w-full border-0 bg-black'
            "
            :src="iframeSrc"
            title="YouTube video player"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
            allowfullscreen
            @load="onIframeLoad"
        />
        <div v-if="!isEmbed" class="mt-1.5 flex min-h-8 flex-wrap items-center justify-end gap-2">
            <span v-t="'actions.playback_speed'" class="text-sm opacity-80" />
            <button
                v-for="rate in speeds"
                :key="rate"
                type="button"
                class="cursor-pointer rounded-md border px-2.5 py-1.5 text-sm leading-none"
                :class="
                    currentRate === rate
                        ? 'border-red-600 bg-red-600 text-white'
                        : 'border-gray-500 bg-dark-400 text-white hover:bg-dark-300'
                "
                @click="setPlaybackSpeed(rate)"
                v-text="rate === 1 ? 'x1' : `x${rate}`"
            />
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";

const STORAGE_SPEED_KEY = "playbackRate";
const STORAGE_PROGRESS_KEY = "watchProgress";
const SPEEDS = [1, 1.25, 1.5, 1.75, 2, 2.5, 3];
const MIN_SAVE_SECONDS = 10;
const MAX_PROGRESS_RATIO = 0.9;
const PROGRESS_POLL_MS = 5000;

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
    isEmbed: Boolean,
});

const iframeEl = ref(null);
const speeds = SPEEDS;
const currentRate = ref(readStoredSpeed());

let lastKnownTime = { currentTime: 0, duration: 0 };
let progressPollTimer = null;
let messageHandler = null;
let visibilityHandler = null;
let pagehideHandler = null;

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
        const raw = localStorage.getItem(STORAGE_SPEED_KEY);
        const n = raw == null ? 1 : Number(raw);
        return Number.isFinite(n) && n > 0 ? n : 1;
    } catch {
        return 1;
    }
}

function isRestorableProgress(currentTime, duration) {
    if (!duration || duration <= 0) return false;
    if (currentTime < MIN_SAVE_SECONDS) return false;
    if (currentTime >= duration * MAX_PROGRESS_RATIO) return false;
    return true;
}

function getStartSeconds(videoId) {
    if (props.startTime > 0) return Math.floor(props.startTime);
    const all = readJSON(STORAGE_PROGRESS_KEY) || {};
    const entry = all[videoId];
    if (entry && isRestorableProgress(entry.currentTime, entry.duration)) {
        return Math.floor(entry.currentTime);
    }
    return 0;
}

function buildEmbedSrc(videoId, startSeconds) {
    const params = new URLSearchParams({
        autoplay: "1",
        enablejsapi: "1",
        origin: location.origin,
        rel: "0",
    });
    if (startSeconds > 0) params.set("start", String(startSeconds));
    return `https://www.youtube-nocookie.com/embed/${videoId}?${params}`;
}

const iframeSrc = computed(() => buildEmbedSrc(props.videoId, getStartSeconds(props.videoId)));

function postCommand(func, args) {
    const win = iframeEl.value?.contentWindow;
    if (!win) return;
    win.postMessage(JSON.stringify({ event: "command", func, args }), "*");
}

function enablePlayerListening() {
    const win = iframeEl.value?.contentWindow;
    if (!win) return;
    win.postMessage(JSON.stringify({ event: "listening", id: 1, channel: "widget" }), "*");
}

function saveWatchProgress(videoId, currentTime, duration) {
    if (!videoId || !duration || duration <= 0) return;
    const all = { ...(readJSON(STORAGE_PROGRESS_KEY) || {}) };

    if (currentTime < MIN_SAVE_SECONDS || currentTime >= duration * MAX_PROGRESS_RATIO) {
        delete all[videoId];
        writeJSON(STORAGE_PROGRESS_KEY, all);
        return;
    }

    all[videoId] = {
        currentTime: Math.floor(currentTime),
        duration: Math.floor(duration),
        updatedAt: Date.now(),
    };
    writeJSON(STORAGE_PROGRESS_KEY, all);
}

function flushProgress() {
    if (!props.videoId || lastKnownTime.duration <= 0) return;
    saveWatchProgress(props.videoId, lastKnownTime.currentTime, lastKnownTime.duration);
}

function pollPlayerState() {
    postCommand("getCurrentTime");
    postCommand("getDuration");
}

function highlightSpeed(rate) {
    currentRate.value = rate;
}

function setPlaybackSpeed(rate) {
    try {
        localStorage.setItem(STORAGE_SPEED_KEY, String(rate));
    } catch {
        /* ignore */
    }
    highlightSpeed(rate);
    postCommand("setPlaybackRate", [rate]);
}

function applyStoredSpeed() {
    const rate = readStoredSpeed();
    highlightSpeed(rate);
    if (rate !== 1) postCommand("setPlaybackRate", [rate]);
}

function seekToSavedPosition(videoId) {
    const start = getStartSeconds(videoId);
    if (start > 0) postCommand("seekTo", [start, true]);
}

function setupMessageListener() {
    if (messageHandler) return;
    messageHandler = event => {
        if (!props.videoId) return;
        if (!event.origin.includes("youtube.com") && !event.origin.includes("youtube-nocookie.com")) return;

        let data;
        try {
            data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
        } catch {
            return;
        }
        if (data?.event !== "infoDelivery" || !data.info) return;

        const { currentTime, duration, playerState } = data.info;
        if (typeof currentTime === "number") lastKnownTime.currentTime = currentTime;
        if (typeof duration === "number" && duration > 0) lastKnownTime.duration = duration;

        // playerState === 0 means "ended": mark as finished (clears saved progress).
        if (playerState === 0 && lastKnownTime.duration > 0) {
            saveWatchProgress(props.videoId, lastKnownTime.duration, lastKnownTime.duration);
        }
    };
    window.addEventListener("message", messageHandler);
}

function startProgressTracking(videoId) {
    stopProgressTracking();
    lastKnownTime = { currentTime: 0, duration: 0 };
    setupMessageListener();

    const tick = () => {
        enablePlayerListening();
        pollPlayerState();
        if (lastKnownTime.duration > 0) {
            saveWatchProgress(videoId, lastKnownTime.currentTime, lastKnownTime.duration);
        }
    };
    progressPollTimer = setInterval(tick, PROGRESS_POLL_MS);
    setTimeout(tick, 800);
    setTimeout(tick, 2000);
}

function stopProgressTracking() {
    if (progressPollTimer) {
        clearInterval(progressPollTimer);
        progressPollTimer = null;
    }
}

function onIframeLoad() {
    const videoId = props.videoId;
    const apply = () => {
        enablePlayerListening();
        applyStoredSpeed();
        pollPlayerState();
    };
    apply();
    setTimeout(apply, 300);
    setTimeout(apply, 1000);
    setTimeout(() => seekToSavedPosition(videoId), 1500);
}

watch(
    () => props.videoId,
    (newId, oldId) => {
        if (newId === oldId) return;
        // Flush progress for the previous video before switching (SPA navigation).
        if (oldId && lastKnownTime.duration > 0) {
            saveWatchProgress(oldId, lastKnownTime.currentTime, lastKnownTime.duration);
        }
        startProgressTracking(newId);
    },
);

onMounted(() => {
    visibilityHandler = () => {
        if (document.visibilityState === "hidden") flushProgress();
    };
    pagehideHandler = () => flushProgress();
    document.addEventListener("visibilitychange", visibilityHandler);
    window.addEventListener("pagehide", pagehideHandler);
    startProgressTracking(props.videoId);
});

onBeforeUnmount(() => {
    flushProgress();
    stopProgressTracking();
    if (messageHandler) window.removeEventListener("message", messageHandler);
    if (visibilityHandler) document.removeEventListener("visibilitychange", visibilityHandler);
    if (pagehideHandler) window.removeEventListener("pagehide", pagehideHandler);
    messageHandler = null;
    visibilityHandler = null;
    pagehideHandler = null;
});
</script>
