<template>
    <div class="relative size-full overflow-hidden bg-black text-white select-none">
        <img
            v-if="thumbnail"
            :src="thumbnail"
            alt=""
            class="absolute inset-0 size-full scale-110 object-cover opacity-40 blur-md"
        />
        <!-- A media element on our own origin keeps playing with the screen off, unlike the embed. -->
        <audio
            ref="audioEl"
            preload="auto"
            @loadedmetadata="onLoadedMetadata"
            @timeupdate="onTimeUpdate"
            @play="setPlaying(true)"
            @pause="setPlaying(false)"
            @waiting="loading = true"
            @playing="loading = false"
            @canplay="loading = false"
            @ended="onEnded"
            @error="onError"
        />

        <div v-if="compact" class="absolute inset-0 flex items-center justify-center">
            <i-fa6-solid-headphones class="text-lg drop-shadow-sm" />
        </div>

        <div v-else class="absolute inset-0 flex flex-col items-center justify-center gap-3 px-4 pt-10 pb-3">
            <!-- SponsorBlock skip / "skipped" notice take the label's place, clear of the controls. -->
            <Transition name="fade" mode="out-in">
                <button
                    v-if="manualSegment"
                    type="button"
                    class="flex h-8 items-center gap-2 rounded-full bg-black/60 px-3.5 text-sm font-medium ring-1 ring-white/30 backdrop-blur-sm hover:bg-black/80"
                    @click="skipSegment(manualSegment)"
                >
                    {{ $t("actions.skip_segment") }}
                    <span class="opacity-70">· {{ categoryLabel(manualSegment.category) }}</span>
                    <i-fa6-solid-forward-step />
                </button>
                <div
                    v-else-if="skippedNotice"
                    class="flex h-8 items-center gap-2 rounded-full bg-black/60 pr-1 pl-3.5 text-sm ring-1 ring-white/20 backdrop-blur-sm"
                >
                    <span>{{ $t("info.skipped") }} {{ categoryLabel(skippedNotice.category).toLowerCase() }}</span>
                    <button
                        v-t="'player.undo'"
                        type="button"
                        class="rounded-full bg-white/15 px-3 py-1 font-medium hover:bg-white/25"
                        @click="undoSkip"
                    />
                </div>
                <div
                    v-else
                    class="flex h-8 items-center gap-2 text-xs font-semibold tracking-wider uppercase opacity-80"
                >
                    <i-fa6-solid-headphones />
                    <span v-t="'player.audio_only'" />
                </div>
            </Transition>
            <p v-if="error" class="max-w-sm text-center text-sm" v-text="error" />
            <template v-else>
                <div class="flex items-center gap-6">
                    <button
                        type="button"
                        class="flex size-10 cursor-pointer items-center justify-center rounded-full hover:bg-white/15"
                        :aria-label="$t('player.back_10')"
                        @click="seekRelative(-SEEK_LARGE)"
                    >
                        <i-fa6-solid-rotate-left />
                    </button>
                    <button
                        type="button"
                        class="flex size-14 cursor-pointer items-center justify-center rounded-full bg-white text-xl text-black shadow-lg"
                        :aria-label="playing ? $t('player.pause') : $t('player.play')"
                        @click="togglePlayPause"
                    >
                        <i-fa6-solid-spinner v-if="loading && playing" class="animate-spin" />
                        <i-fa6-solid-pause v-else-if="playing" />
                        <i-fa6-solid-play v-else class="translate-x-0.5" />
                    </button>
                    <button
                        type="button"
                        class="flex size-10 cursor-pointer items-center justify-center rounded-full hover:bg-white/15"
                        :aria-label="$t('player.forward_10')"
                        @click="seekRelative(SEEK_LARGE)"
                    >
                        <i-fa6-solid-rotate-right />
                    </button>
                </div>
                <div class="flex w-full max-w-xl items-center gap-3 text-xs tabular-nums">
                    <span v-text="timeFormat(current)" />
                    <input
                        type="range"
                        class="h-1 flex-1 cursor-pointer accent-white"
                        min="0"
                        :max="duration || 0"
                        step="1"
                        :value="current"
                        :aria-label="$t('player.seek')"
                        @input="seek(Number($event.target.value), true)"
                    />
                    <span v-text="timeFormat(duration)" />
                </div>
            </template>
        </div>

        <button
            v-if="!compact"
            type="button"
            class="absolute top-2 right-2 flex cursor-pointer items-center gap-2 rounded-full bg-black/55 px-3 py-1.5 text-sm font-medium ring-1 ring-white/20 backdrop-blur-sm hover:bg-black/75"
            @click="$emit('switchtovideo')"
        >
            <i-fa6-solid-tv />
            <span v-t="'player.video'" />
        </button>
    </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from "vue";
import { useI18n } from "vue-i18n";
import { fetchJson, apiUrl } from "@/composables/useApi.js";
import { getPreferenceBoolean } from "@/composables/usePreferences.js";
import { timeFormat } from "@/composables/useFormatting.js";
import { SPEEDS } from "@/composables/usePlayer.js";
import {
    readStoredSpeed,
    writeStoredSpeed,
    getStartSeconds,
    saveWatchProgress,
    categoryLabel,
} from "@/composables/usePlayback.js";

const emit = defineEmits(["timeupdate", "ended", "ratechange", "playingchange", "switchtovideo", "next"]);

const props = defineProps({
    videoId: {
        type: String,
        required: true,
    },
    startTime: {
        type: Number,
        default: 0,
    },
    sponsors: {
        type: Object,
        default: null,
    },
    loop: Boolean,
    keyboard: {
        type: Boolean,
        default: true,
    },
    // Thumbnail only (mini player)
    compact: Boolean,
    // While false the player stays silent: it only preloads (see `preload`) so a
    // switch from the embed, e.g. when the screen turns off, can start at once.
    active: {
        type: Boolean,
        default: true,
    },
    preload: Boolean,
    // The watch page's /streams response, to avoid fetching it again
    streams: {
        type: Object,
        default: null,
    },
    // null: follow the "autoplay video" preference
    autoplay: {
        type: Boolean,
        default: null,
    },
    title: {
        type: String,
        default: "",
    },
    uploader: {
        type: String,
        default: "",
    },
    thumbnail: {
        type: String,
        default: "",
    },
});

const { t } = useI18n();

const SEEK_SMALL = 5;
const SEEK_LARGE = 10;
const PROGRESS_SAVE_MS = 5000;

const audioEl = ref(null);
const current = ref(0);
const duration = ref(0);
const playing = ref(false);
const loading = ref(false);
const error = ref(null);
const currentRate = ref(readStoredSpeed());
const manualSegment = ref(null);
const skippedNotice = ref(null);

let sources = [];
let sourceIndex = 0;
let pendingStart = 0;
let playWhenReady = false;
let refetched = false;
let loadToken = 0;
// Video the current sources belong to
let loadedFor = null;
let lastSave = 0;
let lastPositionState = 0;
let skippedNoticeTimer = null;

// ---- Loading --------------------------------------------------------------

// Audio-only streams when the backend has them, otherwise the muxed 360p
// stream (itag 18): an <audio> element just plays its sound track.
function pickSources(streams) {
    const audio = (streams?.audioStreams ?? [])
        .filter(s => s.url)
        .sort((a, b) => (b.bitrate ?? 0) - (a.bitrate ?? 0))
        .sort((a, b) => Number(!a.mimeType?.includes("mp4")) - Number(!b.mimeType?.includes("mp4")));
    const muxed = (streams?.videoStreams ?? [])
        .filter(s => s.url && !s.videoOnly && s.itag !== -1)
        .sort((a, b) => Number(a.itag !== 18) - Number(b.itag !== 18));
    return [...audio, ...muxed].map(s => s.url);
}

async function load(videoId, start, autoplay, fresh = false) {
    const token = ++loadToken;
    audioEl.value?.pause();
    loadedFor = null;
    error.value = null;
    loading.value = props.active;
    current.value = start;
    duration.value = 0;
    manualSegment.value = null;

    const streams =
        !fresh && props.streams?.id === videoId
            ? props.streams
            : await fetchJson(apiUrl() + "/streams/" + videoId).catch(() => null);
    if (token !== loadToken) return;
    loadedFor = videoId;

    sources = pickSources(streams);
    if (streams?.duration > 0) duration.value = streams.duration;
    if (sources.length === 0) {
        loading.value = false;
        error.value = t("player.audio_unavailable");
        return;
    }
    sourceIndex = 0;
    pendingStart = start;
    playWhenReady = autoplay;
    setSource();
}

function setSource() {
    const el = audioEl.value;
    if (!el) return;
    el.defaultPlaybackRate = currentRate.value;
    el.preload = props.active ? "auto" : "metadata";
    el.src = sources[sourceIndex];
    el.loop = props.loop;
    el.load();
    // Ask right away: browsers allow starting media from a still-active page more
    // readily than from a later callback.
    if (playWhenReady) play();
}

function onLoadedMetadata() {
    const el = audioEl.value;
    if (Number.isFinite(el.duration) && el.duration > 0) duration.value = el.duration;
    if (pendingStart > 0) el.currentTime = pendingStart;
    pendingStart = 0;
    el.playbackRate = currentRate.value;
    updatePositionState(true);
}

function onError() {
    if (!audioEl.value?.src) return;
    if (!props.active) {
        // Reloaded on activation.
        loadedFor = null;
        return;
    }
    const resumeAt = current.value;
    const wasPlaying = playing.value || playWhenReady;
    if (sourceIndex + 1 < sources.length) {
        sourceIndex++;
        pendingStart = resumeAt;
        playWhenReady = wasPlaying;
        setSource();
    } else if (!refetched) {
        // Stream URLs expire after a few hours; fetch fresh ones once.
        refetched = true;
        load(props.videoId, resumeAt, wasPlaying, true);
    } else {
        loading.value = false;
        error.value = t("player.audio_unavailable");
    }
}

// ---- Controls -------------------------------------------------------------

function play() {
    audioEl.value?.play().catch(() => {});
}

function pause() {
    playWhenReady = false;
    audioEl.value?.pause();
}

function togglePlayPause() {
    if (playing.value) pause();
    else {
        playWhenReady = true;
        play();
    }
}

function seek(time, exact = false) {
    const el = audioEl.value;
    const target = Math.max(0, Math.min(exact ? time : Math.floor(time), duration.value || Infinity));
    current.value = target;
    if (el && el.readyState > 0) el.currentTime = target;
    else pendingStart = target;
    emit("timeupdate", target);
    updatePositionState(true);
}

function seekRelative(delta) {
    seek(current.value + delta, true);
}

function setPlaybackSpeed(rate) {
    writeStoredSpeed(rate);
    currentRate.value = rate;
    if (audioEl.value) {
        audioEl.value.defaultPlaybackRate = rate;
        audioEl.value.playbackRate = rate;
    }
    emit("ratechange", rate);
}

function changeSpeed(direction) {
    const next =
        direction > 0
            ? SPEEDS.find(rate => rate > currentRate.value)
            : SPEEDS.findLast(rate => rate < currentRate.value);
    if (next !== undefined) setPlaybackSpeed(next);
}

function isFullScreenEnabled() {
    return Boolean(document.fullscreenElement);
}

// ---- Events ---------------------------------------------------------------

function setPlaying(value) {
    playing.value = value;
    if (!props.active) return;
    if (value) playWhenReady = true;
    emit("playingchange", value);
    if ("mediaSession" in navigator) navigator.mediaSession.playbackState = value ? "playing" : "paused";
    if (!value) flushProgress();
}

function onTimeUpdate() {
    const el = audioEl.value;
    if (!props.active || pendingStart > 0) return;
    current.value = el.currentTime;
    emit("timeupdate", el.currentTime);
    handleSegments(el.currentTime);
    updatePositionState();
    if (playing.value && Date.now() - lastSave > PROGRESS_SAVE_MS) {
        lastSave = Date.now();
        flushProgress();
    }
}

function onEnded() {
    if (!props.active) return;
    saveWatchProgress(props.videoId, duration.value, duration.value);
    emit("ended");
}

function saveProgressNow() {
    if (duration.value > 0) saveWatchProgress(props.videoId, current.value, duration.value);
}

// While inactive the embed owns the progress.
function flushProgress() {
    if (props.active) saveProgressNow();
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

// ---- Lock screen / notification controls -----------------------------------

function updateMetadata() {
    if (!props.active) return;
    if (!("mediaSession" in navigator) || typeof MediaMetadata === "undefined") return;
    navigator.mediaSession.metadata = new MediaMetadata({
        title: props.title,
        artist: props.uploader,
        artwork: props.thumbnail ? [{ src: props.thumbnail }] : [],
    });
}

function updatePositionState(force = false) {
    if (!("mediaSession" in navigator) || !navigator.mediaSession.setPositionState) return;
    if (!force && Date.now() - lastPositionState < 1000) return;
    lastPositionState = Date.now();
    if (!(duration.value > 0)) return;
    try {
        navigator.mediaSession.setPositionState({
            duration: duration.value,
            playbackRate: currentRate.value,
            position: Math.min(current.value, duration.value),
        });
    } catch {
        /* invalid state while loading */
    }
}

const MEDIA_ACTIONS = {
    play: () => {
        playWhenReady = true;
        play();
    },
    pause,
    seekbackward: details => seekRelative(-(details.seekOffset || SEEK_LARGE)),
    seekforward: details => seekRelative(details.seekOffset || SEEK_LARGE),
    seekto: details => seek(details.seekTime, true),
    nexttrack: () => emit("next"),
};

function setMediaActions(enabled) {
    if (!("mediaSession" in navigator)) return;
    for (const [action, handler] of Object.entries(MEDIA_ACTIONS)) {
        try {
            navigator.mediaSession.setActionHandler(action, enabled ? handler : null);
        } catch {
            /* action not supported */
        }
    }
    if (!enabled) navigator.mediaSession.metadata = null;
}

// ---- Keyboard -------------------------------------------------------------

function onKeyDown(event) {
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    const target = event.target;
    if (target instanceof HTMLElement) {
        if (["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) || target.isContentEditable) return;
    }

    const actions = {
        Space: togglePlayPause,
        KeyK: togglePlayPause,
        ArrowLeft: () => seekRelative(-SEEK_SMALL),
        ArrowRight: () => seekRelative(SEEK_SMALL),
        KeyJ: () => seekRelative(-SEEK_LARGE),
        KeyL: () => seekRelative(SEEK_LARGE),
        KeyM: () => audioEl.value && (audioEl.value.muted = !audioEl.value.muted),
        Comma: () => event.shiftKey && changeSpeed(-1),
        Period: () => event.shiftKey && changeSpeed(1),
        Home: () => seek(0),
        End: () => duration.value > 0 && seek(duration.value - 1),
    };
    const digit = /^Digit(\d)$/.exec(event.code);
    if (digit && duration.value > 0) actions[event.code] = () => seek((duration.value * Number(digit[1])) / 10);

    const action = actions[event.code];
    if (!action) return;
    event.preventDefault();
    action();
}

watch(
    () => props.keyboard,
    enabled => {
        if (enabled) document.addEventListener("keydown", onKeyDown);
        else document.removeEventListener("keydown", onKeyDown);
    },
    { immediate: true },
);

// ---- Lifecycle ------------------------------------------------------------

function canPrime(videoId) {
    return props.preload && props.streams?.id === videoId;
}

function activate() {
    const start = getStartSeconds(props.videoId, props.startTime);
    const autoplay = props.autoplay ?? getPreferenceBoolean("playerAutoPlay", true);
    setMediaActions(true);
    updateMetadata();
    if (loadedFor === props.videoId && sources.length > 0 && !error.value) {
        // Preloaded: only seek and play, no network round trip first.
        audioEl.value.preload = "auto";
        playWhenReady = autoplay;
        seek(start, true);
        if (autoplay) play();
    } else {
        load(props.videoId, start, autoplay, loadedFor === props.videoId);
    }
}

function deactivate() {
    pause();
    saveProgressNow();
    setMediaActions(false);
    manualSegment.value = null;
    skippedNotice.value = null;
}

watch(
    () => props.active,
    active => (active ? activate() : deactivate()),
);

// The same <audio> element is reused for the next video, so autoplay-next can
// start while the screen is off.
watch(
    () => props.videoId,
    (videoId, previousId) => {
        if (props.active && duration.value > 0) saveWatchProgress(previousId, current.value, duration.value);
        refetched = false;
        props.sponsors?.segments?.forEach(segment => (segment.skipped = false));
        if (props.active) {
            load(videoId, getStartSeconds(videoId, props.startTime), getPreferenceBoolean("playerAutoPlay", true));
            updateMetadata();
        } else if (canPrime(videoId)) {
            load(videoId, 0, false);
        } else {
            loadToken++;
            loadedFor = null;
            sources = [];
            audioEl.value?.removeAttribute("src");
        }
    },
);

watch(
    () => [props.streams, props.preload],
    () => {
        if (!props.active && loadedFor !== props.videoId && canPrime(props.videoId)) load(props.videoId, 0, false);
    },
);

watch(() => [props.title, props.uploader, props.thumbnail], updateMetadata);

watch(
    () => props.loop,
    loop => audioEl.value && (audioEl.value.loop = loop),
);

watch(
    () => props.sponsors,
    () => props.sponsors?.segments?.forEach(segment => (segment.skipped = false)),
);

function onVisibilityChange() {
    if (document.hidden) flushProgress();
}

onMounted(() => {
    if (props.active) activate();
    else if (canPrime(props.videoId)) load(props.videoId, 0, false);
    document.addEventListener("visibilitychange", onVisibilityChange);
    window.addEventListener("pagehide", flushProgress);
});

onBeforeUnmount(() => {
    flushProgress();
    loadToken++;
    clearTimeout(skippedNoticeTimer);
    audioEl.value?.pause();
    audioEl.value?.removeAttribute("src");
    if (props.active) setMediaActions(false);
    document.removeEventListener("keydown", onKeyDown);
    document.removeEventListener("visibilitychange", onVisibilityChange);
    window.removeEventListener("pagehide", flushProgress);
});

defineExpose({
    seek,
    play: () => {
        playWhenReady = true;
        play();
    },
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
