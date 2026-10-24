<template>
    <div
        v-if="player.videoId"
        ref="rootEl"
        :class="[layoutClass, { 'transition-transform duration-200': !dragging }]"
        :style="layoutStyle"
    >
        <div class="relative shrink-0 overflow-hidden" :class="videoClass">
            <!-- Always mounted (hidden while the embed plays) and not keyed by video:
                 it preloads so the screen-off switch is instant, and its <audio>
                 element carries on to the next video. -->
            <AudioPlayer
                v-show="player.audioMode"
                ref="audioRef"
                :active="player.audioMode"
                :preload="autoAudio"
                :streams="player.streams"
                :video-id="player.videoId"
                :start-time="player.startTime"
                :sponsors="player.sponsors"
                :loop="player.loop"
                :keyboard="isFull && player.audioMode"
                :compact="!isFull"
                :autoplay="player.resumePlaying"
                :title="player.title"
                :uploader="player.uploader"
                :thumbnail="player.thumbnail"
                @timeupdate="time => (player.currentTime = time)"
                @ended="onPlayerEnded"
                @ratechange="rate => (player.rate = rate)"
                @playingchange="playing => (player.playing = playing)"
                @switchtovideo="setAudioMode(false)"
                @next="skipToNext"
            />
            <YouTubeEmbed
                v-if="!player.audioMode"
                :key="`${player.videoId}-${player.playerEpoch}`"
                ref="videoRef"
                :video-id="player.videoId"
                :start-time="player.startTime"
                :sponsors="player.sponsors"
                :loop="player.loop"
                :keyboard="isFull"
                :autoplay="player.resumePlaying"
                @timeupdate="time => (player.currentTime = time)"
                @ended="onPlayerEnded"
                @ratechange="rate => (player.rate = rate)"
                @playingchange="playing => (player.playing = playing)"
            />
            <!-- The mobile mini player is too small to use YouTube's controls; a tap expands it. -->
            <button
                v-if="!isFull && isMobileLayout"
                type="button"
                class="absolute inset-0"
                :aria-label="$t('player.expand')"
                @click="expand"
            />
            <button
                v-if="isFull && isMobileLayout && !immersive"
                type="button"
                class="absolute top-1 left-1 flex size-10 items-center justify-center rounded-full text-white drop-shadow-[0_1px_2px_rgb(0_0_0/0.8)]"
                :aria-label="$t('player.minimize')"
                :title="$t('player.minimize')"
                @click="minimizePlayer(router)"
            >
                <i-fa6-solid-chevron-down class="text-lg" />
            </button>
        </div>

        <div v-if="!isFull" class="flex min-w-0 flex-1 items-center gap-1 pr-1.5 lg:py-1.5 lg:pl-1">
            <button type="button" class="min-w-0 flex-1 cursor-pointer px-3 text-left" @click="expand">
                <div class="truncate text-sm font-medium" v-text="player.title || '…'" />
                <div class="truncate text-xs text-muted" v-text="player.uploader" />
            </button>
            <button
                type="button"
                class="btn btn-icon btn-ghost"
                :aria-label="player.playing ? $t('player.pause') : $t('player.play')"
                @click="embed?.togglePlayPause()"
            >
                <i-fa6-solid-pause v-if="player.playing" />
                <i-fa6-solid-play v-else />
            </button>
            <button type="button" class="btn btn-icon btn-ghost" :aria-label="$t('actions.close')" @click="closePlayer">
                <i-fa6-solid-xmark />
            </button>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, watchEffect, nextTick, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import YouTubeEmbed from "./YouTubeEmbed.vue";
import AudioPlayer from "./AudioPlayer.vue";
import {
    player,
    embed,
    isMobileLayout,
    onPlayerEnded,
    closePlayer,
    minimizePlayer,
    setAudioMode,
    skipToNext,
} from "@/composables/usePlayer.js";
import { usePreferenceBoolean } from "@/composables/usePreferences.js";

const router = useRouter();

const SWIPE_START_PX = 10;
const SWIPE_MINIMIZE_PX = 110;

const rootEl = ref(null);
const rect = ref(null);
// Touch devices only: a narrow, wide desktop window is "landscape" too.
const coarsePointer = window.matchMedia("(pointer: coarse)").matches;
const landscapeQuery = window.matchMedia("(orientation: landscape)");
const isLandscape = ref(landscapeQuery.matches);
landscapeQuery.addEventListener("change", e => (isLandscape.value = e.matches));
const dragging = ref(false);
let frame = 0;
let touchStart = null;

const isFull = computed(() => player.mode === "full");

// Turning a phone sideways on the watch page fills the screen with the video,
// like the YouTube app.
const immersive = computed(
    () =>
        Boolean(player.videoId) &&
        isFull.value &&
        coarsePointer &&
        isMobileLayout.value &&
        isLandscape.value &&
        !player.audioMode,
);

const layoutClass = computed(() => {
    if (immersive.value) return "fixed inset-0 z-50 bg-black";
    if (isFull.value) {
        return isMobileLayout.value
            ? "fixed inset-x-0 top-0 z-40 aspect-video max-h-svh bg-black"
            : // below the sticky header, which it scrolls under
              ["absolute z-30 overflow-hidden rounded-xl", { invisible: !rect.value }];
    }
    return isMobileLayout.value
        ? "fixed inset-x-0 bottom-[calc(3.5rem+var(--bottom-inset))] z-40 flex h-16 items-center border-t border-(--border) bg-(--surface-raised)"
        : "fixed right-4 bottom-4 z-40 flex w-[400px] flex-col overflow-hidden rounded-xl border border-(--border) bg-(--surface-raised) shadow-(--shadow)";
});

const videoClass = computed(() => {
    if (isFull.value) return "size-full";
    return isMobileLayout.value ? "aspect-video h-full" : "aspect-video w-full";
});

const layoutStyle = computed(() => {
    if (immersive.value) return null;
    if (isFull.value && isMobileLayout.value && player.dragOffset > 0) {
        return { transform: `translateY(${player.dragOffset}px) scale(${1 - player.dragOffset / 1500})` };
    }
    if (isFull.value && !isMobileLayout.value && rect.value) {
        const { top, left, width, height } = rect.value;
        return { top: `${top}px`, left: `${left}px`, width: `${width}px`, height: `${height}px` };
    }
    return null;
});

const audioRef = ref(null);
const videoRef = ref(null);
watchEffect(() => (embed.value = player.audioMode ? audioRef.value : videoRef.value));

// Phones: YouTube's embed stops when the screen turns off, so hand over to the
// audio player then, and back to the video when the page is visible again.
const autoAudioPreference = usePreferenceBoolean("autoAudioWhenHidden", true);
const autoAudio = computed(() => coarsePointer && autoAudioPreference.value);
let switchedForHidden = false;

function onVisibilityChange() {
    if (document.hidden) {
        if (autoAudio.value && player.videoId && !player.audioMode && player.playing) {
            setAudioMode(true);
            switchedForHidden = true;
        }
    } else if (switchedForHidden) {
        switchedForHidden = false;
        if (player.audioMode) setAudioMode(false);
    }
}

onMounted(() => document.addEventListener("visibilitychange", onVisibilityChange));

function expand() {
    if (player.watchUrl) router.push(player.watchUrl);
}

// ---- Desktop: follow the watch page's placeholder --------------------------

function trackSlot() {
    const el = player.slot;
    const r = el?.getBoundingClientRect();
    const next =
        r && r.width > 0 ? { top: r.top + scrollY, left: r.left + scrollX, width: r.width, height: r.height } : null;
    const prev = rect.value;
    if (
        !next !== !prev ||
        (next &&
            (next.top !== prev.top ||
                next.left !== prev.left ||
                next.width !== prev.width ||
                next.height !== prev.height))
    ) {
        rect.value = next;
    }
    frame = requestAnimationFrame(trackSlot);
}

// ---- Mobile: swipe down to minimize ----------------------------------------

function onTouchStart(event) {
    touchStart = null;
    if (event.touches.length !== 1 || window.scrollY > 0) return;
    if (event.target.closest?.("[data-no-swipe]")) return;
    touchStart = { x: event.touches[0].clientX, y: event.touches[0].clientY };
}

function onTouchMove(event) {
    if (!touchStart) return;
    const dx = event.touches[0].clientX - touchStart.x;
    const dy = event.touches[0].clientY - touchStart.y;
    if (!dragging.value) {
        if (dy > SWIPE_START_PX && dy > Math.abs(dx)) dragging.value = true;
        else if (Math.abs(dx) > SWIPE_START_PX || dy < -SWIPE_START_PX) touchStart = null;
        return;
    }
    event.preventDefault();
    player.dragOffset = Math.max(0, dy - SWIPE_START_PX);
}

function onTouchEnd() {
    touchStart = null;
    if (!dragging.value) return;
    dragging.value = false;
    if (player.dragOffset > SWIPE_MINIMIZE_PX) minimizePlayer(router);
    else player.dragOffset = 0;
}

function addSwipe() {
    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchmove", onTouchMove, { passive: false });
    window.addEventListener("touchend", onTouchEnd);
    window.addEventListener("touchcancel", onTouchEnd);
    // Pulling down at the top of the page would otherwise trigger pull-to-refresh.
    document.documentElement.style.overscrollBehaviorY = "none";
}

function removeSwipe() {
    window.removeEventListener("touchstart", onTouchStart);
    window.removeEventListener("touchmove", onTouchMove);
    window.removeEventListener("touchend", onTouchEnd);
    window.removeEventListener("touchcancel", onTouchEnd);
    document.documentElement.style.overscrollBehaviorY = "";
    dragging.value = false;
    touchStart = null;
}

watch(
    () => Boolean(player.videoId) && isFull.value && !isMobileLayout.value,
    track => {
        cancelAnimationFrame(frame);
        if (track) trackSlot();
        else rect.value = null;
    },
    { immediate: true },
);

watch(
    () => Boolean(player.videoId) && isFull.value && isMobileLayout.value && !immersive.value,
    swipe => (swipe ? addSwipe() : removeSwipe()),
    { immediate: true },
);

// Real fullscreen also hides the browser's bars, but browsers only allow it shortly
// after a tap; otherwise the fixed full-window layout above is the fallback.
watch(immersive, async enabled => {
    await nextTick();
    if (enabled && !document.fullscreenElement) {
        rootEl.value?.requestFullscreen?.({ navigationUI: "hide" }).catch(() => {});
    } else if (!enabled && document.fullscreenElement && document.fullscreenElement === rootEl.value) {
        document.exitFullscreen().catch(() => {});
    }
});

onBeforeUnmount(() => {
    document.removeEventListener("visibilitychange", onVisibilityChange);
    cancelAnimationFrame(frame);
    removeSwipe();
});
</script>
